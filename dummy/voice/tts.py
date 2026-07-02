"""Voice output (TTS) module for Jarvis — Phase 3.

Primary path:
- pyttsx3 for offline, low-latency speech output

Optional higher-quality path:
- Coqui TTS for synthesized WAV files that can be played back with playsound

The module keeps the implementation local to `voice/` so it can be integrated
incrementally without disturbing the existing chat/STT backend.
"""
from __future__ import annotations

import queue
import re
import tempfile
import threading
import time
import pythoncom
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    import pyttsx3
except Exception:  # pragma: no cover - import-time guard
    pyttsx3 = None  # type: ignore

try:
    from playsound import playsound
except Exception:  # pragma: no cover - import-time guard
    playsound = None  # type: ignore

try:
    from TTS.api import TTS as CoquiTTS
except Exception:  # pragma: no cover - import-time guard
    CoquiTTS = None  # type: ignore


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
        # Keep TTS chunks short enough for natural pauses.
        if len(sentence) <= 140:
            chunks.append(sentence)
            continue

        parts = re.split(r"[,;:]\s+", sentence)
        for part in parts:
            part = part.strip()
            if part:
                chunks.append(part)

    return chunks


@dataclass(order=True)
class _SpeechRequest:
    priority_value: int
    sequence: int
    text: str
    done_event: Optional[threading.Event] = None


class TTSManager:
    """Manage Jarvis speech output using pyttsx3 with an optional Coqui path."""

    def __init__(
        self,
        voice_index: int = 0,
        rate: int = 175,
        volume: float = 1.0,
        coqui_model: str = "tts_models/en/ljspeech/tacotron2-DDC",
    ) -> None:
        self.voice_index = voice_index
        self.rate = rate
        self._volume = self._clamp_volume(volume)
        self.coqui_model = coqui_model

        self._engine = None
        self._coqui = None
        self._coqui_cache: Dict[str, str] = {}
        self._queue: "queue.PriorityQueue[_SpeechRequest]" = queue.PriorityQueue()
        self._sequence = 0
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._busy = threading.Event()
        self._lock = threading.Lock()
        self._ready = False

    @property
    def is_speaking(self) -> bool:
        return self._busy.is_set()

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = self._clamp_volume(value)
        if self._engine is not None:
            self._engine.setProperty("volume", self._volume)

    def _clamp_volume(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _ensure_engine(self):
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 is not installed. Install it with pip.")
        if self._engine is None:
            print("[TTS] Initializing COM")
            pythoncom.CoInitialize()
            print("[TTS] Initializing pyttsx3")
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty("voices") or []
            if voices:
                index = min(max(self.voice_index, 0), len(voices) - 1)
                self._engine.setProperty("voice", voices[index].id)
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self._volume)

    def _ensure_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        self._stop_event.clear()

        def _loop() -> None:
            while not self._stop_event.is_set():
                try:
                    request = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                self._busy.set()
                try:
                    self._speak_impl(request.text)
                finally:
                    self._busy.clear()
                    if request.done_event:
                        request.done_event.set()

        self._worker = threading.Thread(target=_loop, daemon=True)
        self._worker.start()

    def _ensure_coqui(self):
        if CoquiTTS is None:
            raise RuntimeError("Coqui TTS is not installed. Install package `TTS`.")
        if self._coqui is None:
            self._coqui = CoquiTTS(model_name=self.coqui_model, progress_bar=False, gpu=False)

    def warm_common_phrases(self) -> None:
        """Preload speech resources for common Jarvis phrases."""
        for phrase in COMMON_JARVIS_PHRASES:
            self._precache_phrase(phrase)

    def _precache_phrase(self, phrase: str) -> None:
        if CoquiTTS is None:
            self._ensure_engine()
            return

        normalized = clean_response_text(phrase)
        if normalized in self._coqui_cache:
            return

        try:
            path = self.synthesize(normalized)
            self._coqui_cache[normalized] = path
        except Exception:
            # Cache warm-up should never break speech output.
            return

    def preprocess(self, text: str) -> List[str]:
        return split_text_for_tts(text)

    def speak(self, text: str, priority: str = "normal") -> None:
        """Speak text synchronously."""
        self._ensure_worker()
        self.stop_current_speech()
        self._drain_queue()
        done_event = threading.Event()
        self._enqueue(text, priority=priority, done_event=done_event)
        done_event.wait()

    def speak_async(self, text: str, priority: str = "normal") -> None:
        """Speak text without blocking the caller."""
        self._ensure_worker()
        self._enqueue(text, priority=priority, done_event=None)

    def interrupt_and_speak(self, text: str) -> None:
        """Stop current speech and replace it with urgent text."""
        self._ensure_worker()
        self.stop_current_speech()
        self._drain_queue()
        self._enqueue(text, priority="urgent", done_event=None)

    def stop_current_speech(self) -> None:
        self._ensure_engine()
        try:
            self._engine.stop()
        except Exception:
            pass

    def _enqueue(self, text: str, priority: str, done_event: Optional[threading.Event]) -> None:
        priority_value = self._priority_value(priority)
        with self._lock:
            self._sequence += 1
            request = _SpeechRequest(priority_value, self._sequence, text, done_event)
            self._queue.put(request)

    def _drain_queue(self) -> None:
        with self._lock:
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

    def _priority_value(self, priority: str) -> int:
        mapping = {
            "urgent": 0,
            "high": 1,
            "normal": 2,
            "low": 3,
        }
        return mapping.get(priority, 2)

    def _speak_impl(self, text: str) -> None:
        clean = clean_response_text(text)
        if not clean:
            return

        chunks = self.preprocess(clean)
        if not chunks:
            return

        if self._has_coqui_available() and clean in self._coqui_cache:
            self.play_audio(self._coqui_cache[clean])
            return

        self._ensure_engine()
        self.stop_current_speech()

        for index, chunk in enumerate(chunks):
            self._engine.say(chunk)
            self._engine.runAndWait()
            if index < len(chunks) - 1:
                time.sleep(0.18)

    def _has_coqui_available(self) -> bool:
        return CoquiTTS is not None

    def synthesize(self, text: str) -> str:
        """Synthesise text to a WAV file using Coqui TTS."""
        self._ensure_coqui()
        normalized = clean_response_text(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            output_path = temp_file.name
        self._coqui.tts_to_file(text=normalized, file_path=output_path)
        return output_path

    def play_audio(self, file_path: str) -> None:
        """Play a WAV file using playsound when available."""
        if playsound is None:
            raise RuntimeError("playsound is not installed. Install it with pip.")
        playsound(file_path)

    def preload_common_phrases(self) -> None:
        """Alias kept for readability."""
        self.warm_common_phrases()

    def shutdown(self) -> None:
        self._stop_event.set()
        try:
            self.stop_current_speech()
        except Exception:
            pass
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)


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