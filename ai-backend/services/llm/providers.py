import json
import logging
import time
import httpx
from typing import Dict, List, Any, Optional, Iterator
from .base import LLMProvider
from .config import LLMConfig

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str, config: Optional[LLMConfig] = None):
        self._model_name = model_name
        self.config = config or LLMConfig()
        self.base_url = self.config.ollama_url.rstrip("/")
        self.timeout = httpx.Timeout(connect=10.0, read=self.config.timeout, write=30.0, pool=10.0)
        # Reuse a single HTTP client for connection pooling and performance
        self._client = httpx.Client(timeout=self.timeout)

    @property
    def model_name(self) -> str:
        return self._model_name

    def initialize(self) -> bool:
        """Warm up model by calling the endpoint with a cheap generation."""
        try:
            # Check model availability first
            tags_resp = self._client.get(f"{self.base_url}/api/tags")
            if tags_resp.status_code == 200:
                models = [m.get("name") for m in tags_resp.json().get("models", [])]
                if self._model_name not in models and f"{self._model_name}:latest" not in models:
                    logger.warning(f"[OllamaProvider] Model {self._model_name} might not be pulled.")
            
            # Send small generate request to trigger model load/warmup
            payload = {
                "model": self._model_name,
                "prompt": "ping",
                "stream": False,
                "options": {"num_predict": 1}
            }
            resp = self._client.post(f"{self.base_url}/api/generate", json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"[OllamaProvider] Initialization failed for {self._model_name}: {e}")
            return False

    def health(self) -> bool:
        try:
            resp = self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def _execute_request_stream(self, endpoint: str, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.stream("POST", url, json=payload, timeout=self.timeout) as response:
                if response.status_code != 200:
                    response_text = response.read().decode("utf-8", errors="replace")
                    if "out of memory" in response_text.lower():
                        raise RuntimeError(f"OOM: Out of memory on Ollama for model {self._model_name}")
                    raise httpx.HTTPStatusError(
                        f"Ollama returned {response.status_code}: {response_text}",
                        request=response.request,
                        response=response
                    )
                for line in response.iter_lines():
                    if not line:
                        continue
                    yield json.loads(line)
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Connection refused: could not connect to Ollama at {self.base_url}.") from exc
        except httpx.ReadTimeout as exc:
            raise TimeoutError(f"Timeout: model {self._model_name} took too long to respond.") from exc
        except Exception as exc:
            if "out of memory" in str(exc).lower():
                raise RuntimeError(f"OOM: Out of memory on Ollama for model {self._model_name}") from exc
            raise exc

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        payload = {
            "model": self._model_name,
            "prompt": prompt if system_prompt is None else f"{system_prompt}\n\n{prompt}",
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                "num_ctx": kwargs.get("num_ctx", self.config.context_length)
            }
        }
        if kwargs.get("format"):
            payload["format"] = kwargs["format"]
            
        url = f"{self.base_url}/api/generate"
        try:
            resp = self._client.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Connection refused: could not connect to Ollama at {self.base_url}.") from exc
        except httpx.ReadTimeout as exc:
            raise TimeoutError(f"Timeout: model {self._model_name} took too long to respond.") from exc
        except Exception as exc:
            if "out of memory" in str(exc).lower():
                raise RuntimeError(f"OOM: Out of memory on Ollama for model {self._model_name}") from exc
            raise exc

    def stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Iterator[str]:
        payload = {
            "model": self._model_name,
            "prompt": prompt if system_prompt is None else f"{system_prompt}\n\n{prompt}",
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                "num_ctx": kwargs.get("num_ctx", self.config.context_length)
            }
        }
        if kwargs.get("format"):
            payload["format"] = kwargs["format"]
            
        for chunk in self._execute_request_stream("/api/generate", payload):
            content = chunk.get("response", "")
            if content:
                yield content
            if chunk.get("done"):
                break

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                "num_ctx": kwargs.get("num_ctx", self.config.context_length)
            }
        }
        if kwargs.get("format"):
            payload["format"] = kwargs["format"]
            
        url = f"{self.base_url}/api/chat"
        try:
            resp = self._client.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            message = resp.json().get("message", {})
            return message.get("content", "").strip()
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Connection refused: could not connect to Ollama at {self.base_url}.") from exc
        except httpx.ReadTimeout as exc:
            raise TimeoutError(f"Timeout: model {self._model_name} took too long to respond.") from exc
        except Exception as exc:
            if "out of memory" in str(exc).lower():
                raise RuntimeError(f"OOM: Out of memory on Ollama for model {self._model_name}") from exc
            raise exc

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                "num_ctx": kwargs.get("num_ctx", self.config.context_length)
            }
        }
        if kwargs.get("format"):
            payload["format"] = kwargs["format"]
            
        for chunk in self._execute_request_stream("/api/chat", payload):
            message = chunk.get("message", {})
            content = message.get("content", "")
            if content:
                yield content
            if chunk.get("done"):
                break

    def structured_output(self, prompt: str, schema: Any, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        response_text = self.generate(prompt, system_prompt=system_prompt, format="json", **kwargs)
        
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end <= 0:
            raise ValueError(f"Malformed JSON: could not locate any JSON boundaries in: {response_text}")
        json_text = response_text[start:end]
        
        parsed = json.loads(json_text)
        if callable(schema):
            schema(parsed)
        return parsed

    def cancel(self) -> None:
        pass

    def shutdown(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    def supports_tools(self) -> bool:
        return False

    def supports_streaming(self) -> bool:
        return True

    def supports_json(self) -> bool:
        return True


class HermesProvider(OllamaProvider):
    def __init__(self, config: Optional[LLMConfig] = None):
        cfg = config or LLMConfig()
        super().__init__(cfg.default_model, cfg)


class QwenProvider(OllamaProvider):
    def __init__(self, config: Optional[LLMConfig] = None):
        cfg = config or LLMConfig()
        super().__init__(cfg.fallback_model, cfg)
