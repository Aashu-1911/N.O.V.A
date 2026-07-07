"""
Utilities for talking to a locally running Ollama instance.

This module keeps the Ollama chat client isolated from routing and intent parsing.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Iterable, Optional

import httpx

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
        self.timeout = timeout

    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[Iterable[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        history = list(conversation_history or [])[-10:]
        return ([{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_message}])

    def _stream_request(self, payload: Dict[str, object]) -> List[str]:
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

    def _stream_generate(self, payload: Dict[str, object]) -> List[str]:
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


def send_message(user_message: str, conversation_history: Optional[Iterable[Dict[str, str]]] = None):
    return _DEFAULT_CLIENT.send_message(user_message, conversation_history)
