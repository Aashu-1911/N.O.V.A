import logging
import threading
import json
import re
from typing import Dict, List, Any, Optional, Iterator, Callable
from .config import LLMConfig
from .base import LLMProvider
from .providers import HermesProvider, QwenProvider
from .benchmark import run_benchmarked_stream, BenchmarkMetrics

logger = logging.getLogger(__name__)

class LLMService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LLMService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
        self.config = LLMConfig(config_path)
        self.default_provider = HermesProvider(self.config)
        self.fallback_provider = QwenProvider(self.config)
        self.active_provider = self.default_provider
        self._initialized = True
        
        # Warm the models asynchronously on startup to avoid blocking
        self.warm_models()

    def warm_models(self) -> None:
        """Asynchronously warm up both default and fallback models to load them into memory."""
        def _warm_worker():
            logger.info("[LLMService] Pre-warming default provider (Hermes)...")
            h_ok = self.default_provider.initialize()
            logger.info(f"[LLMService] Hermes pre-warm status: {h_ok}")
            
            logger.info("[LLMService] Pre-warming fallback provider (Qwen)...")
            q_ok = self.fallback_provider.initialize()
            logger.info(f"[LLMService] Qwen pre-warm status: {q_ok}")

        threading.Thread(target=_warm_worker, daemon=True).start()

    def select_model(self, selection_mode: str = "AUTO") -> None:
        """Select provider based on selection mode. AUTO checks health status and selects fastest provider."""
        if selection_mode == "Hermes":
            self.active_provider = self.default_provider
            logger.info(f"[LLMService] Explicitly set active model to default ({self.default_provider.model_name})")
        elif selection_mode == "Qwen":
            self.active_provider = self.fallback_provider
            logger.info(f"[LLMService] Explicitly set active model to fallback ({self.fallback_provider.model_name})")
        elif selection_mode == "AUTO":
            logger.info("[LLMService] Auto-selecting model based on health rankings...")
            # Check default provider health
            if self.default_provider.health():
                self.active_provider = self.default_provider
                logger.info(f"[LLMService] Auto-selected default model: {self.default_provider.model_name} (Healthy)")
            elif self.fallback_provider.health():
                self.active_provider = self.fallback_provider
                logger.info(f"[LLMService] Auto-selected fallback model: {self.fallback_provider.model_name} (Default Unhealthy)")
            else:
                logger.warning("[LLMService] All configured providers reported unhealthy! Defaulting to Hermes.")
                self.active_provider = self.default_provider

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text with default-to-fallback auto-recovery."""
        def _action(provider):
            return provider.generate(prompt, system_prompt=system_prompt, **kwargs)
        return self._execute_with_fallback(_action)

    def stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Iterator[str]:
        """Stream response chunks with default-to-fallback auto-recovery."""
        try:
            # First try default/active provider
            for chunk in self.active_provider.stream(prompt, system_prompt=system_prompt, **kwargs):
                yield chunk
        except Exception as e:
            logger.warning(f"[LLMService] Streaming failed on active provider ({self.active_provider.model_name}). Retrying with fallback: {e}")
            fallback_target = self.fallback_provider if self.active_provider != self.fallback_provider else self.default_provider
            try:
                for chunk in fallback_target.stream(prompt, system_prompt=system_prompt, **kwargs):
                    yield chunk
            except Exception as final_exc:
                logger.error(f"[LLMService] Both providers failed during stream: {final_exc}")
                raise final_exc

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat conversation with default-to-fallback auto-recovery."""
        def _action(provider):
            return provider.chat(messages, **kwargs)
        return self._execute_with_fallback(_action)

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """Stream chat conversation chunks with default-to-fallback auto-recovery."""
        try:
            for chunk in self.active_provider.stream_chat(messages, **kwargs):
                yield chunk
        except Exception as e:
            logger.warning(f"[LLMService] Chat streaming failed on active provider. Retrying with fallback: {e}")
            fallback_target = self.fallback_provider if self.active_provider != self.fallback_provider else self.default_provider
            try:
                for chunk in fallback_target.stream_chat(messages, **kwargs):
                    yield chunk
            except Exception as final_exc:
                logger.error(f"[LLMService] Both providers failed during chat stream: {final_exc}")
                raise final_exc

    def structured_output(self, prompt: str, schema: Any = None, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Request structured JSON, validating structure. Retries once with same provider, then falls back."""
        try:
            # Attempt 1: primary/active provider
            return self.active_provider.structured_output(prompt, schema=schema, system_prompt=system_prompt, **kwargs)
        except (json.JSONDecodeError, ValueError) as json_err:
            logger.warning(f"[LLMService] Structured JSON validation failed on first attempt ({self.active_provider.model_name}): {json_err}. Retrying once...")
            try:
                # Attempt 2: retry on active provider
                return self.active_provider.structured_output(prompt, schema=schema, system_prompt=system_prompt, **kwargs)
            except Exception as retry_err:
                logger.warning(f"[LLMService] Structured JSON retry failed on active provider: {retry_err}. Falling back to Qwen...")
        except Exception as general_err:
            logger.warning(f"[LLMService] Provider error during structured output: {general_err}. Falling back to Qwen...")

        # Fallback to alternative provider
        fallback_target = self.fallback_provider if self.active_provider != self.fallback_provider else self.default_provider
        try:
            return fallback_target.structured_output(prompt, schema=schema, system_prompt=system_prompt, **kwargs)
        except Exception as final_err:
            logger.error(f"[LLMService] Both default and fallback providers failed to generate valid structured output: {final_err}")
            raise RuntimeError(f"Failed to generate valid structured JSON from all LLM providers: {final_err}") from final_err

    def stream_to_tts(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Iterator[str]:
        """Stream LLM response and speak completed sentences asynchronously via TTS as they arrive."""
        from voice import speak_async
        from adapters.voice_adapter import format_for_voice
        
        sentence_buffer = ""
        # Regex to split on sentence boundaries (. ! ?) followed by whitespace, keeping delimiters
        sentence_end_re = re.compile(r'([^.!?]+[.!?]+)\s*')
        
        for chunk in self.stream(prompt, system_prompt=system_prompt, **kwargs):
            yield chunk
            sentence_buffer += chunk
            
            # Look for completed sentences in the buffer
            matches = list(sentence_end_re.finditer(sentence_buffer))
            if matches:
                last_end = 0
                for match in matches:
                    sentence = match.group(1).strip()
                    if sentence:
                        spoken = format_for_voice(sentence)
                        if spoken:
                            logger.info(f"[LLMService] Streaming TTS: speak_async({spoken!r})")
                            speak_async(spoken)
                    last_end = match.end()
                sentence_buffer = sentence_buffer[last_end:]
                
        # Speak any remaining text in buffer
        remaining = sentence_buffer.strip()
        if remaining:
            spoken = format_for_voice(remaining)
            if spoken:
                logger.info(f"[LLMService] Streaming TTS (final buffer): speak_async({spoken!r})")
                speak_async(spoken)

    def _execute_with_fallback(self, action: Callable[[LLMProvider], Any]) -> Any:
        try:
            return action(self.active_provider)
        except Exception as e:
            logger.warning(f"[LLMService] Provider {self.active_provider.model_name} failed. Retrying with fallback: {e}")
            fallback_target = self.fallback_provider if self.active_provider != self.fallback_provider else self.default_provider
            try:
                return action(fallback_target)
            except Exception as final_exc:
                logger.error(f"[LLMService] Both default and fallback providers failed: {final_exc}")
                raise final_exc

    def cancel(self) -> None:
        self.active_provider.cancel()
        self.fallback_provider.cancel()

    def shutdown(self) -> None:
        self.default_provider.shutdown()
        self.fallback_provider.shutdown()
