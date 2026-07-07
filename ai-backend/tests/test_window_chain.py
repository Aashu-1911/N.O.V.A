"""Chain execution and pronoun resolution tests for window management."""

import sys
import os
from unittest.mock import patch

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.command_chain import execute_chain, _update_context
from core.execution_context import ExecutionContext
from core.command_executor import execute_command


class TestWindowChainContext:
    def test_update_context_sets_window_fields(self):
        ec = ExecutionContext()
        result = {
            "status": "success",
            "intent": "maximize_window",
            "payload": {"window_title": "Google Chrome", "window_handle": 42},
        }
        _update_context(ec, "maximize chrome", result)
        assert ec.last_window == "Google Chrome"
        assert ec.last_window_handle == 42

    def test_list_windows_does_not_update_context(self):
        ec = ExecutionContext(last_window="Old", last_window_handle=1)
        result = {
            "status": "success",
            "intent": "list_windows",
            "payload": {"windows": ["A", "B"]},
        }
        _update_context(ec, "list windows", result)
        assert ec.last_window == "Old"
        assert ec.last_window_handle == 1


class TestOpenAndMaximizeChain:
    @patch("handlers.app_handler.open_application", return_value=True)
    @patch("handlers.window_handler.window_manager.maximize_window")
    def test_open_chrome_and_maximize_it(self, mock_maximize, mock_open):
        from managers.window_manager import WindowOperationResult

        mock_maximize.return_value = WindowOperationResult(
            success=True,
            matched_title="Google Chrome",
            handle=99,
        )

        response = execute_command("Open Chrome and maximize it")
        assert response["intent"] == "chain"
        assert response["status"] == "success"
        results = response["payload"]["results"]
        assert len(results) == 2
        assert results[0]["intent"] == "open_application"
        assert results[1]["intent"] == "maximize_window"
        mock_maximize.assert_called_once_with("chrome")


class TestThreeStepChain:
    @patch("handlers.app_handler.open_application", return_value=True)
    @patch("handlers.window_handler.window_manager.maximize_window")
    @patch("handlers.window_handler.window_manager.restore_window")
    def test_three_step_chain(self, mock_restore, mock_maximize, mock_open):
        from managers.window_manager import WindowOperationResult

        mock_maximize.return_value = WindowOperationResult(
            success=True, matched_title="Google Chrome", handle=1
        )
        mock_restore.return_value = WindowOperationResult(
            success=True, matched_title="Google Chrome", handle=1
        )

        response = execute_command("Open Chrome then maximize it then restore it")
        assert response["status"] == "success"
        assert len(response["payload"]["results"]) == 3
        mock_maximize.assert_called_once()
        mock_restore.assert_called_once()


class TestDependentSkip:
    @patch("handlers.app_handler.open_application", return_value=False)
    @patch("handlers.window_handler.window_manager.maximize_window")
    def test_open_fails_maximize_skipped(self, mock_maximize, mock_open):
        response = execute_command("Open Chrome and maximize it")
        results = response["payload"]["results"]
        assert results[0]["status"] == "error"
        assert results[1]["status"] == "skipped"
        assert response["status"] == "error"
        mock_maximize.assert_not_called()


class TestPronounNoContext:
    @patch("handlers.window_handler.window_manager.maximize_window")
    def test_maximize_it_without_context(self, mock_maximize):
        response = execute_command("Maximize it")
        assert response["status"] == "error"
        assert response["reply"] == "No window name provided."
        mock_maximize.assert_not_called()
