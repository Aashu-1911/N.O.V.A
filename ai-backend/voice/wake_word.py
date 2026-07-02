DEFAULT_WAKE_WORDS = ["hey nova", "nova", "ok nova"]


def contains_wake_word(text: str, wake_words=None) -> bool:
    if not text:
        return False

    candidates = wake_words or DEFAULT_WAKE_WORDS
    normalized = text.lower()
    return any(wake_word in normalized for wake_word in candidates)
