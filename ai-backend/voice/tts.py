"""Voice output (TTS) module for Jarvis — Phase 3.

Completely refactored to use Piper TTS and sounddevice/soundfile.
"""
from __future__ import annotations

import re
import logging
from typing import List, Optional
from tts.service import TTSService

logger = logging.getLogger(__name__)

COMMON_JARVIS_PHRASES = [
    "Yes, I'm here",
    "On it",
    "Done",
    "I couldn't understand that, could you repeat?",
    "Task added successfully",
]


def clean_response_text(text: str) -> str:
    """Remove simple markdown and normalize spacing for TTS."""
    cleaned = text.replace("**", "")
    cleaned = cleaned.replace("#", "")
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def split_text_for_tts(text: str) -> List[str]:
    """Split a response into short natural chunks suitable for streaming TTS."""
    cleaned = clean_response_text(text)
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: List[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= 140:
            chunks.append(sentence)
            continue

        parts = re.split(r"[,;:]\s+", sentence)
        for part in parts:
            part = part.strip()
            if part:
                chunks.append(part)

    return chunks


class TTSManager:
    """Bridge to the new TTSService using Piper TTS backend."""

    def __init__(
        self,
        voice_index: int = 0,
        rate: int = 175,
        volume: float = 1.0,
        coqui_model: str = "",
    ) -> None:
        self.service = TTSService()
        self.service.volume = volume
        if rate != 175 and rate > 0:
            self.service.engine.length_scale = 175.0 / rate

    @property
    def is_speaking(self) -> bool:
        return self.service.is_speaking

    @property
    def volume(self) -> float:
        return self.service.volume

    @volume.setter
    def volume(self, value: float) -> None:
        self.service.volume = value

    def _ensure_worker(self) -> None:
        self.service._ensure_worker()

    def speak(self, text: str, priority: str = "normal") -> None:
        self.service.speak(text, priority)

    def speak_async(self, text: str, priority: str = "normal") -> None:
        self.service.speak_async(text, priority)

    def interrupt_and_speak(self, text: str) -> None:
        self.service.interrupt_and_speak(text)

    def stop_current_speech(self) -> None:
        self.service.stop()

    def stop(self) -> None:
        self.service.stop()

    def synthesize(self, text: str) -> str:
        return self.service.synthesize(text)

    def play_audio(self, file_path: str) -> None:
        self.service.play_audio(file_path)

    def shutdown(self) -> None:
        self.service.shutdown()

    def warm_common_phrases(self) -> None:
        pass

    def preload_common_phrases(self) -> None:
        pass


_default_tts_manager = TTSManager()


def speak(text: str) -> None:
    _default_tts_manager.speak(text)


def speak_async(text: str) -> None:
    _default_tts_manager.speak_async(text)


def interrupt_and_speak(text: str) -> None:
    _default_tts_manager.interrupt_and_speak(text)


def synthesize(text: str) -> str:
    return _default_tts_manager.synthesize(text)


def play_audio(file_path: str) -> None:
    _default_tts_manager.play_audio(file_path)


__all__ = [
    "COMMON_JARVIS_PHRASES",
    "TTSManager",
    "clean_response_text",
    "interrupt_and_speak",
    "play_audio",
    "speak",
    "speak_async",
    "split_text_for_tts",
    "synthesize",
]