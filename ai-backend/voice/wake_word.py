"""Wake word detection for the Voice_Module.

Provides a simple, case-insensitive substring match to determine whether
transcribed text contains a wake word.  No ML model or confidence scoring
is used in V1 — plain string containment is fast, predictable, and easy to
test.
"""
from __future__ import annotations

from typing import List, Optional

DEFAULT_WAKE_WORDS: List[str] = ["jarvis", "assistant", "hey nova"]


def contains_wake_word(text: str, wake_words: Optional[List[str]] = None) -> bool:
    """
    Simple wake word detection — check if text contains any wake word.

    Args:
        text: Input text to check (typically a Whisper transcript).
        wake_words: List of wake words to look for.  Defaults to
            ``["jarvis", "assistant", "hey nova"]``.

    Returns:
        ``True`` if *text* contains at least one wake word
        (case-insensitive substring match), ``False`` otherwise.
    """
    if not text:
        return False

    if wake_words is None:
        wake_words = DEFAULT_WAKE_WORDS

    text_lower = text.lower()
    return any(word.lower() in text_lower for word in wake_words)
