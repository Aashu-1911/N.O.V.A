"""
Utilities for talking to a locally running Ollama instance.

Phase 1 keeps the pieces in one module for simplicity:
- ConversationManager stores short-term chat memory
- parse_intent extracts simple task/assistant intents
- send_message streams Jarvis responses from Ollama
"""

from __future__ import annotations

import json
import os
import re
from collections import deque
from typing import Deque, Dict, Generator, Iterable, List, Optional
from urllib.parse import urlparse

import httpx


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
FALLBACK_MODEL = "qwen3:8b"
CHAT_ENDPOINT = "/api/chat"
GENERATE_ENDPOINT = "/api/generate"

SUPPORTED_MODELS = {OLLAMA_MODEL, "llama3.2", "qwen3:8b"}

SYSTEM_PROMPT = (
    "You are Jarvis, a smart personal assistant. "
    "Be helpful, concise, and practical. "
    "You know the user has a task tracker and can help manage tasks, progress, "
    "web browsing, and screen control. "
    "Respond in 1-3 sentences unless extra detail is clearly needed. "
    "You can recognize these intents when relevant: add_task, update_task, "
    "complete_task, show_progress, browse_web, control_screen, answer_question, reminder."
)


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama server is unavailable."""


class ConversationManager:
    """Keeps the latest conversation messages in memory."""

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self._messages: Deque[Dict[str, str]] = deque(maxlen=max_messages)

    def add_message(self, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        self._messages.append({"role": role, "content": content.strip()})

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        history = list(self._messages)
        if limit is None or limit >= len(history):
            return history
        return history[-limit:]

    def clear(self) -> None:
        self._messages.clear()


from urllib.parse import urlparse
import re
from typing import Optional

def _extract_url(text: str) -> Optional[str]:

    # Real URLs
    url_match = re.search(
        r"(https?://[^\s]+|www\.[^\s]+)",
        text,
        flags=re.IGNORECASE
    )

    if url_match:
        candidate = url_match.group(1)

        if not candidate.startswith(("http://", "https://")):
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)

        if parsed.netloc:
            return candidate

    # Website names
    website_name = match_website(text)

    if website_name:
        return website_name

        return None


def _extract_priority(text: str) -> Optional[str]:
    priority_match = re.search(r"\b(low|medium|high|urgent)\b", text, flags=re.IGNORECASE)
    return priority_match.group(1).lower() if priority_match else None


def _extract_category(text: str) -> Optional[str]:
    category_patterns = [
        r"(?:category|for)\s+(?:is\s+)?([a-zA-Z][a-zA-Z0-9_-]+)",
        r"\b(work|personal|study|health|home|shopping|finance)\b",
    ]
    for pattern in category_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return None


def _extract_date(text: str) -> Optional[str]:
    patterns = [
        r"\b(today|tomorrow|tonight|weekend|next week|next month)\b",
        r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _extract_task_name(text: str, intent: str) -> Optional[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    intent_patterns = {
        "add_task": [
            r"(?:add|create|make)\s+(?:a\s+)?task(?:\s+to)?[:\-]?\s*(.+)",
            r"(?:add)\s+task\s+(.+)",
            r"(?:add)\s+it\s+as\s+(?:a\s+)?task(?:\s+to)?\s*(.+)",
            r"(?:remember to|remind me to)\s+(.+)",
        ],
        "complete_task": [
            r"(?:complete|finish|mark done|mark as done)\s+(?:task\s+)?(.+)",
            r"(?:task\s+)?(.+?)\s+(?:is\s+)?(?:done|completed|finished)",
        ],
        "update_task": [
            r"(?:update|edit|change|modify)\s+(?:task\s+)?(.+)",
        ],
        "reminder": [
            r"(?:remind me to|set a reminder to)\s+(.+)",
        ],
    }

    for pattern in intent_patterns.get(intent, []):
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            task_name = match.group(1).strip(" .")
            task_name = re.sub(r"^(?:to\s+)+", "", task_name, flags=re.IGNORECASE)
            return task_name or None

    return None


def parse_intent(text: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Parse a user message into a lightweight intent + entities payload.

    Returns:
        {
            "intent": "<intent_name>",
            "entities": {
                "task_name": ...,
                "category": ...,
                "priority": ...,
                "url": ...,
                "date": ...
            }
        }
    """

    normalized = text.strip().lower()

    intent = "answer_question"
    if re.search(r"\b(complete|finish|done|mark done|mark as done|completed)\b", normalized):
        intent = "complete_task"
    elif re.search(r"\b(update|edit|change|modify)\b", normalized):
        intent = "update_task"
    elif re.search(r"\b(add|create|new task|remember to|remind me to)\b", normalized):
        intent = "add_task" if "remind me" not in normalized else "reminder"
    elif re.search(r"\b(stats|statistics|progress|summary|status)\b", normalized):
        intent = "show_stats"
    elif _extract_url(text) or re.search(r"\b(open|visit|website|site|browser)\b", normalized):
        intent = "open_website"
    elif re.search(r"\b(remind|reminder)\b", normalized):
        intent = "reminder"

    entities = {
        "task_name": _extract_task_name(text, intent),
        "category": _extract_category(text),
        "priority": _extract_priority(text),
        "url": _extract_url(text),
        "date": _extract_date(text),
    }

    task_name = entities.get("task_name")
    date_value = entities.get("date")
    if task_name and date_value:
        cleaned_task_name = re.sub(
            rf"\s*(?:on|by|for)?\s*{re.escape(date_value)}$",
            "",
            task_name,
            flags=re.IGNORECASE,
        ).strip(" .")
        entities["task_name"] = cleaned_task_name or task_name

    return {"intent": intent, "entities": entities}


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
        return (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + history
            + [{"role": "user", "content": user_message}]
        )

    def _stream_request(self, payload: Dict[str, object]) -> Generator[str, None, None]:
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
                        yield content

                    if chunk.get("done"):
                        break
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

    def _stream_generate(self, payload: Dict[str, object]) -> Generator[str, None, None]:
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
                        yield content

                    if chunk.get("done"):
                        break
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
    ) -> Generator[str, None, None]:
        payload = {
            "model": self.model,
            "messages": self._build_messages(user_message, conversation_history),
            "stream": True,
        }

        try:
            yield from self._stream_request(payload)
        except RuntimeError as exc:
            if "api/chat not found" in str(exc).lower():
                generate_payload = {
                    "model": self.model,
                    "prompt": self._messages_to_prompt(
                        self._build_messages(user_message, conversation_history)
                    ),
                    "stream": True,
                }
                try:
                    yield from self._stream_generate(generate_payload)
                    return
                except RuntimeError:
                    if self.model != FALLBACK_MODEL:
                        fallback_payload = {
                            "model": FALLBACK_MODEL,
                            "prompt": generate_payload["prompt"],
                            "stream": True,
                        }
                        yield from self._stream_generate(fallback_payload)
                        return
                    raise

            if self.model != FALLBACK_MODEL:
                fallback_payload = {**payload, "model": FALLBACK_MODEL}
                try:
                    yield from self._stream_request(fallback_payload)
                    return
                except RuntimeError:
                    pass
            raise

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        lines = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                lines.append(f"System: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            else:
                lines.append(f"User: {content}")
        lines.append("Assistant:")
        return "\n".join(lines)


_default_client = OllamaClient()


def send_message(
    user_message: str,
    conversation_history: Optional[Iterable[Dict[str, str]]] = None,
):
    return _default_client.send_message(user_message, conversation_history)
