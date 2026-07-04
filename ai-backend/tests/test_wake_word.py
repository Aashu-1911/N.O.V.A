"""Unit tests for voice/wake_word.py — task 10.3."""
import pytest

from voice.wake_word import contains_wake_word, DEFAULT_WAKE_WORDS


class TestDefaultWakeWords:
    def test_default_list_contains_expected_words(self):
        assert "jarvis" in DEFAULT_WAKE_WORDS
        assert "assistant" in DEFAULT_WAKE_WORDS
        assert "hey nova" in DEFAULT_WAKE_WORDS

    def test_default_list_length(self):
        assert len(DEFAULT_WAKE_WORDS) == 3


class TestContainsWakeWord:
    # --- default wake words ---

    def test_detects_jarvis(self):
        assert contains_wake_word("hey jarvis, set a timer") is True

    def test_detects_assistant(self):
        assert contains_wake_word("ok assistant please help") is True

    def test_detects_hey_nova(self):
        assert contains_wake_word("hey nova what's the weather") is True

    def test_no_wake_word_returns_false(self):
        assert contains_wake_word("open the browser please") is False

    # --- case insensitivity ---

    def test_case_insensitive_upper(self):
        assert contains_wake_word("JARVIS turn off the lights") is True

    def test_case_insensitive_mixed(self):
        assert contains_wake_word("Hey Assistant, play music") is True

    def test_case_insensitive_hey_nova(self):
        assert contains_wake_word("HEY NOVA stop") is True

    # --- custom wake words ---

    def test_custom_wake_word_detected(self):
        assert contains_wake_word("ok computer, open files", wake_words=["computer"]) is True

    def test_custom_wake_word_not_present(self):
        assert contains_wake_word("hey nova", wake_words=["computer"]) is False

    def test_custom_wake_words_multiple(self):
        assert contains_wake_word("hello there", wake_words=["hello", "world"]) is True

    # --- edge cases ---

    def test_empty_string_returns_false(self):
        assert contains_wake_word("") is False

    def test_whitespace_only_returns_false(self):
        # whitespace doesn't match any wake word
        assert contains_wake_word("   ") is False

    def test_none_wake_words_uses_defaults(self):
        assert contains_wake_word("jarvis", wake_words=None) is True

    def test_empty_wake_words_list_returns_false(self):
        assert contains_wake_word("jarvis", wake_words=[]) is False

    def test_wake_word_as_substring(self):
        # "assistant" embedded mid-word — still matches (substring search)
        assert contains_wake_word("myassistantapp", wake_words=["assistant"]) is True
