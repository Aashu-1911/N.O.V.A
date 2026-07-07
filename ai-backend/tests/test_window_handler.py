"""Unit tests for handlers/window_handler.py"""

import sys
import os
from unittest.mock import patch

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from handlers.window_handler import (
    _resolve_window,
    _execute_window_action,
    handle_focus_window,
    handle_maximize_window,
    handle_minimize_window,
    handle_restore_window,
    handle_list_windows,
    handle_get_active_window,
)
from managers.window_manager import WindowOperationResult


def _ok_result(title="Google Chrome", handle=12345):
    return WindowOperationResult(success=True, matched_title=title, handle=handle)


class TestResolveWindow:
    def test_entity_takes_priority(self):
        assert _resolve_window("chrome", {"last_window": "telegram"}) == "chrome"

    def test_falls_back_to_context(self):
        assert _resolve_window(None, {"last_window": "Google Chrome"}) == "Google Chrome"

    def test_returns_none_when_both_absent(self):
        assert _resolve_window(None, None) is None
        assert _resolve_window(None, {}) is None


class TestExecuteWindowAction:
    @patch("handlers.window_handler.window_manager.focus_window", return_value=_ok_result())
    def test_happy_path(self, mock_fn):
        result = _execute_window_action("focus", mock_fn, "chrome", None)
        assert result["status"] == "success"
        assert result["reply"] == "Focused Google Chrome."
        assert result["payload"]["window_title"] == "Google Chrome"
        assert result["payload"]["window_handle"] == 12345

    @patch(
        "handlers.window_handler.window_manager.focus_window",
        return_value=WindowOperationResult(success=False, reason="Window not found"),
    )
    def test_not_found(self, mock_fn):
        result = _execute_window_action("focus", mock_fn, "missing", None)
        assert result["status"] == "error"
        assert result["reply"] == "Window 'missing' was not found."

    def test_no_name_guard(self):
        result = _execute_window_action("focus", lambda x: _ok_result(), None, None)
        assert result["status"] == "error"
        assert result["reply"] == "No window name provided."

    @patch("handlers.window_handler.window_manager.focus_window", return_value=_ok_result())
    def test_pronoun_via_context(self, mock_fn):
        result = _execute_window_action("focus", mock_fn, None, {"last_window": "Google Chrome"})
        assert result["status"] == "success"
        mock_fn.assert_called_once_with("Google Chrome")

    @patch("handlers.window_handler.window_manager.focus_window", side_effect=RuntimeError("boom"))
    def test_exception_contained(self, mock_fn):
        result = _execute_window_action("focus", mock_fn, "chrome", None)
        assert result["status"] == "error"
        assert result["reply"] == "Unable to focus window."


class TestSingleWindowHandlers:
    @patch("handlers.window_handler.window_manager.maximize_window", return_value=_ok_result())
    def test_maximize(self, mock_fn):
        result = handle_maximize_window({"window_name": "chrome"})
        assert result["reply"] == "Maximized Google Chrome."

    @patch("handlers.window_handler.window_manager.minimize_window", return_value=_ok_result())
    def test_minimize(self, mock_fn):
        result = handle_minimize_window({"window_name": "chrome"})
        assert result["reply"] == "Minimized Google Chrome."

    @patch("handlers.window_handler.window_manager.restore_window", return_value=_ok_result())
    def test_restore(self, mock_fn):
        result = handle_restore_window({"window_name": "chrome"})
        assert result["reply"] == "Restored Google Chrome."


class TestListWindowsHandler:
    @patch(
        "handlers.window_handler.window_manager.list_windows",
        return_value=["Google Chrome", "Telegram Desktop"],
    )
    def test_non_empty(self, mock_fn):
        result = handle_list_windows({})
        assert result["status"] == "success"
        assert result["reply"] == "There are 2 open windows."
        assert len(result["payload"]["windows"]) == 2

    @patch("handlers.window_handler.window_manager.list_windows", return_value=[])
    def test_empty(self, mock_fn):
        result = handle_list_windows({})
        assert result["reply"] == "No open windows found."
        assert result["payload"]["windows"] == []


class TestGetActiveWindowHandler:
    @patch(
        "handlers.window_handler.window_manager.get_active_window",
        return_value=WindowOperationResult(
            success=True,
            matched_title="Visual Studio Code",
            handle=99,
            process_name="Code.exe",
        ),
    )
    def test_active_window_present(self, mock_fn):
        result = handle_get_active_window({})
        assert result["status"] == "success"
        assert "Visual Studio Code" in result["reply"]
        assert result["payload"]["process_name"] == "Code.exe"

    @patch(
        "handlers.window_handler.window_manager.get_active_window",
        return_value=WindowOperationResult(success=True, matched_title=None),
    )
    def test_no_active_window(self, mock_fn):
        result = handle_get_active_window({})
        assert result["reply"] == "No active window detected."
        assert result["payload"]["window_title"] is None
