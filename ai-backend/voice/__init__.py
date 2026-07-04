"""
Voice module public API.

This module exposes the clean public interface for all voice operations:
- VoiceInputManager: manages microphone capture, transcription, and command callbacks
- TTSManager: manages text-to-speech synthesis and playback
- speak: synchronous text-to-speech (blocks until playback completes)
- speak_async: asynchronous text-to-speech (returns immediately)
- synthesize: synthesize text to an audio file path without playing
- contains_wake_word: utility to detect wake words in transcribed text

Internal implementation details (TTSManager internals, audio helpers,
clean_response_text, play_audio, interrupt_and_speak, DEFAULT_WAKE_WORDS)
are intentionally not exported here.
"""
from __future__ import annotations

from .stt import VoiceInputManager
from .tts import TTSManager, speak as _speak, speak_async as _speak_async, synthesize as _synthesize
from .wake_word import contains_wake_word

__all__ = [
    "VoiceInputManager",
    "TTSManager",
    "speak",
    "speak_async",
    "synthesize",
    "contains_wake_word",
]


def speak(text: str) -> None:
    """Synthesize *text* and play audio synchronously.

    Blocks the calling thread until playback is complete.

    Args:
        text: The text to convert to speech. Markdown formatting is
              stripped automatically before synthesis.
    """
    _speak(text)


def speak_async(text: str) -> None:
    """Synthesize *text* and play audio without blocking the caller.

    The speech is queued for playback in a background thread.  Control
    returns to the caller immediately.

    Args:
        text: The text to convert to speech. Markdown formatting is
              stripped automatically before synthesis.
    """
    _speak_async(text)


def synthesize(text: str) -> str:
    """Synthesize *text* to an audio file and return the file path.

    The file is written to a temporary location. The caller is
    responsible for deleting it when no longer needed.

    Args:
        text: The text to synthesize. Markdown formatting is stripped
              automatically before synthesis.

    Returns:
        Absolute path to the generated WAV file.

    Raises:
        RuntimeError: If the Coqui TTS back-end is not available.
    """
    return _synthesize(text)
