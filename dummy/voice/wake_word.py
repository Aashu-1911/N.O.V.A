DEFAULT_WAKE_WORDS = ["hey jarvis", "jarvis", "ok jarvis"]


def contains_wake_word(text: str, wake_words=None) -> bool:
    if not text:
        return False

    candidates = wake_words or DEFAULT_WAKE_WORDS
    normalized = text.lower()
    return any(wake_word in normalized for wake_word in candidates)
