"""
Utilities for talking to a locally running Ollama instance.

This module keeps the Ollama chat client isolated from routing and intent parsing.
"""

from __future__ import annotations

import json
import os
import time
import logging
from typing import Dict, List, Iterable, Optional

import httpx
import logging

logger = logging.getLogger(__name__)

from core.conversation import ConversationManager
from core.prompt_builder import build_ollama_system_prompt

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
FALLBACK_MODEL = "qwen3:8b"
CHAT_ENDPOINT = "/api/chat"
GENERATE_ENDPOINT = "/api/generate"

SUPPORTED_MODELS = {OLLAMA_MODEL, "llama3.2", "qwen3:8b"}

SYSTEM_PROMPT = build_ollama_system_prompt()


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama server is unavailable."""


class OllamaClient:
    """Small streaming client for a local Ollama chat model."""

    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model if model in SUPPORTED_MODELS else OLLAMA_MODEL
        # Use a Timeout object: 10s to connect, 300s to read (for slow CPU inference)
        self.timeout = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)

    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[Iterable[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        # Keep only the last 6 exchanges (12 messages) to stay within context limits.
        # Large history causes Ollama HTTP 500 when the model context window overflows.
        history = list(conversation_history or [])[-6:]
        return ([{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_message}])

    def _execute_with_retry(self, send_fn, payload: Dict[str, object]) -> List[str]:
        from config import VOICE_CONFIG
        from voice.metrics import VOICE_METRICS
        import httpx
        
        max_retries = VOICE_CONFIG.get("retry_count", 2)
        retry_delay = VOICE_CONFIG.get("retry_delay", 0.25)
        
        attempts = max_retries + 1
        last_exc = None
        
        for attempt in range(attempts):
            try:
                return send_fn(payload)
            except Exception as exc:
                last_exc = exc
                
                is_retryable = False
                status_code = None
                
                if isinstance(exc, httpx.HTTPStatusError):
                    status_code = exc.response.status_code
                elif isinstance(exc, RuntimeError) and isinstance(exc.__cause__, httpx.HTTPStatusError):
                    status_code = exc.__cause__.response.status_code
                elif isinstance(exc, RuntimeError) and isinstance(exc.__context__, httpx.HTTPStatusError):
                    status_code = exc.__context__.response.status_code
                elif isinstance(exc, RuntimeError) and "status 500" in str(exc):
                    status_code = 500
                elif isinstance(exc, RuntimeError) and "status 502" in str(exc):
                    status_code = 502
                elif isinstance(exc, RuntimeError) and "status 503" in str(exc):
                    status_code = 503
                    
                if status_code in (500, 502, 503):
                    is_retryable = True
                elif isinstance(exc, (OllamaConnectionError, httpx.ConnectError, httpx.RemoteProtocolError, ConnectionResetError)):
                    is_retryable = True
                elif isinstance(exc, (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException, TimeoutError)):
                    is_retryable = True
                elif isinstance(exc, RuntimeError) and any(t in str(exc) for t in ("connection", "timeout", "too long to respond")):
                    is_retryable = True
                
                if is_retryable and attempt < attempts - 1:
                    VOICE_METRICS.increment_retries(1)
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(f"[OLLAMA] Request failed (attempt {attempt + 1}/{attempts}). Retrying in {delay}s. Error: {exc}")
                    time.sleep(delay)
                else:
                    raise exc
        
        raise last_exc

    def _stream_request(self, payload: Dict[str, object]) -> List[str]:
        return self._execute_with_retry(self._stream_request_impl, payload)

    def _stream_generate(self, payload: Dict[str, object]) -> List[str]:
        return self._execute_with_retry(self._stream_generate_impl, payload)

    def _stream_request_impl(self, payload: Dict[str, object]) -> List[str]:
        """Stream a chat request and return all chunks as a list.
        
        The HTTP connection is fully consumed and closed before returning.
        This prevents connection state leakage between requests.
        """
        chunks: List[str] = []
        try:
            print("CHAT URL:", f"{self.base_url}{CHAT_ENDPOINT}")
            print("MODEL:", payload.get("model"))
            with httpx.stream(
                "POST",
                f"{self.base_url}{CHAT_ENDPOINT}",
                json=payload,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    chunk = json.loads(line)
                    message = chunk.get("message", {})
                    content = message.get("content", "")
                    if content:
                        chunks.append(content)

                    if chunk.get("done"):
                        break
            
            return chunks
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                "Could not connect to Ollama at http://localhost:11434. "
                "Make sure Ollama is installed, running, and the model is pulled."
            ) from exc
        except httpx.ReadTimeout as exc:
            raise RuntimeError(
                "Ollama took too long to respond. The model may be loading or your "
                "hardware is too slow. Try a smaller model like 'qwen3:1.7b'."
            ) from exc
        except httpx.HTTPStatusError as exc:
            response_text = ""
            try:
                response_text = exc.response.read().decode("utf-8", errors="replace")
            except Exception:
                response_text = ""

            if exc.response.status_code == 404:
                raise RuntimeError("Ollama chat endpoint /api/chat not found.") from exc

            raise RuntimeError(
                f"Ollama request failed with status {exc.response.status_code}: "
                f"{response_text}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Received an invalid streaming response from Ollama.") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

    def _stream_generate_impl(self, payload: Dict[str, object]) -> List[str]:
        """Stream a generate request and return all chunks as a list.
        
        The HTTP connection is fully consumed and closed before returning.
        This prevents connection state leakage between requests.
        """
        chunks: List[str] = []
        try:
            print("GENERATE URL:", f"{self.base_url}{GENERATE_ENDPOINT}")
            print("MODEL:", payload.get("model"))
            with httpx.stream(
                "POST",
                f"{self.base_url}{GENERATE_ENDPOINT}",
                json=payload,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    chunk = json.loads(line)
                    content = chunk.get("response", "")
                    if content:
                        chunks.append(content)

                    if chunk.get("done"):
                        break
            
            return chunks
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                "Could not connect to Ollama at http://localhost:11434. "
                "Make sure Ollama is installed, running, and the model is pulled."
            ) from exc
        except httpx.ReadTimeout as exc:
            raise RuntimeError(
                "Ollama took too long to respond. The model may be loading or your "
                "hardware is too slow. Try a smaller model like 'qwen3:1.7b'."
            ) from exc
        except httpx.HTTPStatusError as exc:
            response_text = ""
            try:
                response_text = exc.response.read().decode("utf-8", errors="replace")
            except Exception:
                response_text = ""
            raise RuntimeError(
                f"Ollama request failed with status {exc.response.status_code}: "
                f"{response_text}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Received an invalid streaming response from Ollama.") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

    def send_message(
        self,
        user_message: str,
        conversation_history: Optional[Iterable[Dict[str, str]]] = None,
    ) -> List[str]:
        """Send a chat message and return all response chunks.
        
        Returns a list of strings rather than a generator to ensure
        the HTTP connection is properly closed before returning.
        """
        payload = {
            "model": self.model,
            "messages": self._build_messages(user_message, conversation_history),
            "stream": True,
            "options": {"num_ctx": 2048},  # cap context to prevent OOM/500 on CPU
        }

        return self._stream_request(payload)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[str]:
        """Generate text and return all response chunks.
        
        Returns a list of strings rather than a generator to ensure
        the HTTP connection is properly closed before returning.
        """
        payload = {
            "model": self.model,
            "prompt": prompt if system_prompt is None else f"{system_prompt}\n\n{prompt}",
            "stream": True,
        }

        return self._stream_generate(payload)


_DEFAULT_CLIENT = OllamaClient()


def send_message(user_message: str, conversation_history: Optional[Iterable[Dict[str, str]]] = None) -> List[str]:
    import re
    from services.llm.service import LLMService
    from voice.metrics import request_context
    
    service = LLMService()
    service.select_model("AUTO")
    
    is_voice = getattr(request_context, "metrics", None) is not None
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    if conversation_history:
        history = list(conversation_history)[-6:]
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    chunks = []
    try:
        if is_voice:
            from voice import speak_async
            from adapters.voice_adapter import format_for_voice
            sentence_buffer = ""
            sentence_end_re = re.compile(r'([^.!?]+[.!?]+)\s*')
            
            for chunk in service.stream_chat(messages):
                chunks.append(chunk)
                sentence_buffer += chunk
                matches = list(sentence_end_re.finditer(sentence_buffer))
                if matches:
                    last_end = 0
                    for match in matches:
                        sentence = match.group(1).strip()
                        if sentence:
                            spoken = format_for_voice(sentence)
                            if spoken:
                                logger.info(f"[ollama_service] Streaming TTS: speak_async({spoken!r})")
                                speak_async(spoken)
                        last_end = match.end()
                    sentence_buffer = sentence_buffer[last_end:]
            
            remaining = sentence_buffer.strip()
            if remaining:
                spoken = format_for_voice(remaining)
                if spoken:
                    logger.info(f"[ollama_service] Streaming TTS (final): speak_async({spoken!r})")
                    speak_async(spoken)
        else:
            for chunk in service.stream_chat(messages):
                chunks.append(chunk)
        return chunks
    except Exception as e:
        logger.warning(f"[ollama_service] Provider {service.active_provider.model_name} failed. Retrying with fallback: {e}")
        fallback_target = service.fallback_provider if service.active_provider != service.fallback_provider else service.default_provider
        try:
            fallback_chunks = list(fallback_target.stream_chat(messages))
            return fallback_chunks
        except Exception as final_exc:
            logger.error(f"[ollama_service] Both default and fallback providers failed: {final_exc}")
            raise final_exc


def generate_text(prompt: str, system_prompt: Optional[str] = None) -> List[str]:
    from services.llm.service import LLMService
    service = LLMService()
    service.select_model("AUTO")
    
    chunks = []
    try:
        for chunk in service.stream(prompt, system_prompt=system_prompt):
            chunks.append(chunk)
        return chunks
    except Exception as e:
        logger.warning(f"[ollama_service] Provider {service.active_provider.model_name} failed on generate. Retrying with fallback: {e}")
        fallback_target = service.fallback_provider if service.active_provider != service.fallback_provider else service.default_provider
        try:
            return list(fallback_target.stream(prompt, system_prompt=system_prompt))
        except Exception as final_exc:
            logger.error(f"[ollama_service] Both default and fallback providers failed on generate: {final_exc}")
            raise final_exc
