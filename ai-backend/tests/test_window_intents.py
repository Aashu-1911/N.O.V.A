"""Intent detection and regression tests for window management intents."""

import sys
import os

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.intent_parser import parse_intent

_WINDOW_INTENTS = {
    "focus_window",
    "maximize_window",
    "minimize_window",
    "restore_window",
    "list_windows",
    "get_active_window",
}


POSITIVE_CASES = [
    ("maximize chrome", "maximize_window", "chrome"),
    ("minimize telegram", "minimize_window", "telegram"),
    ("restore vs code", "restore_window", "vs code"),
    ("focus chrome", "focus_window", "chrome"),
    ("bring telegram to front", "focus_window", "telegram"),
    ("switch to vs code", "focus_window", "vs code"),
    ("list windows", "list_windows", None),
    ("show open windows", "list_windows", None),
    ("what windows are open", "list_windows", None),
    ("active window", "get_active_window", None),
    ("current window", "get_active_window", None),
    ("which window is focused", "get_active_window", None),
    ("maximize it", "maximize_window", None),
]


DISAMBIGUATION_CASES = [
    "maximize volume",
    "restore default settings",
    "maximize brightness",
]


REGRESSION_CASES = [
    ("open chrome", "open_application"),
    ("close telegram", "close_application"),
    ("play music", "media_control"),
]


class TestPositiveWindowIntents:
    @pytest.mark.parametrize("text,expected_intent,expected_window_name", POSITIVE_CASES)
    def test_positive_detection(self, text, expected_intent, expected_window_name):
        result = parse_intent(text)
        assert result["intent"] == expected_intent
        assert result["confidence"] == 0.95
        assert result["entities"].get("window_name") == expected_window_name


class TestDisambiguation:
    @pytest.mark.parametrize("text", DISAMBIGUATION_CASES)
    def test_does_not_produce_window_intent(self, text):
        result = parse_intent(text)
        assert result["intent"] not in _WINDOW_INTENTS


class TestRegression:
    @pytest.mark.parametrize("text,expected_intent", REGRESSION_CASES)
    def test_existing_intents_unaffected(self, text, expected_intent):
        result = parse_intent(text)
        assert result["intent"] == expected_intent
