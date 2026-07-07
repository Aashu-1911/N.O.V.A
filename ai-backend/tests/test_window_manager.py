"""Unit tests for managers/window_manager.py"""

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from managers.window_manager import (
    WindowOperationResult,
    focus_window,
    maximize_window,
    minimize_window,
    restore_window,
    list_windows,
    get_active_window,
    _find_window_obj,
)
from utils.constants import SYSTEM_WINDOW_TITLES, WINDOW_MATCH_THRESHOLD


def _make_win(title: str, hwnd: int = 12345):
    win = MagicMock()
    win.title = title
    win._hWnd = hwnd
    return win


class TestFindWindowObj:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_exact_title_match(self, mock_get_all):
        mock_get_all.return_value = [_make_win("Google Chrome")]
        result = _find_window_obj("Google Chrome")
        assert result is not None
        assert result.title == "Google Chrome"

    @patch("managers.window_manager.gw.getAllWindows")
    def test_fuzzy_match(self, mock_get_all):
        mock_get_all.return_value = [_make_win("Google Chrome")]
        result = _find_window_obj("chrome")
        assert result is not None

    @patch("managers.window_manager.gw.getAllWindows")
    def test_below_threshold_returns_none(self, mock_get_all):
        mock_get_all.return_value = [_make_win("Completely Unrelated Application Title")]
        result = _find_window_obj("xyz")
        assert result is None

    @patch("managers.window_manager.gw.getAllWindows")
    def test_filters_system_windows(self, mock_get_all):
        mock_get_all.return_value = [_make_win("Program Manager")]
        result = _find_window_obj("Program Manager")
        assert result is None

    @patch("managers.window_manager.gw.getAllWindows")
    def test_filters_short_titles(self, mock_get_all):
        mock_get_all.return_value = [_make_win("A")]
        result = _find_window_obj("A")
        assert result is None


class TestFocusWindow:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_happy_path(self, mock_get_all):
        win = _make_win("Google Chrome", 999)
        mock_get_all.return_value = [win]
        result = focus_window("chrome")
        assert result.success is True
        assert result.matched_title == "Google Chrome"
        assert result.handle == 999
        win.activate.assert_called_once()

    @patch("managers.window_manager.gw.getAllWindows")
    def test_not_found(self, mock_get_all):
        mock_get_all.return_value = []
        result = focus_window("nonexistent")
        assert result.success is False
        assert result.reason == "Window not found"

    @patch("managers.window_manager.gw.getAllWindows")
    def test_exception_contained(self, mock_get_all):
        win = _make_win("Google Chrome")
        win.activate.side_effect = RuntimeError("OS error")
        mock_get_all.return_value = [win]
        result = focus_window("chrome")
        assert result.success is False
        assert "OS error" in result.reason


class TestMaximizeWindow:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_calls_maximize(self, mock_get_all):
        win = _make_win("Telegram Desktop")
        mock_get_all.return_value = [win]
        result = maximize_window("telegram")
        assert result.success is True
        win.maximize.assert_called_once()


class TestMinimizeWindow:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_calls_minimize(self, mock_get_all):
        win = _make_win("Telegram Desktop")
        mock_get_all.return_value = [win]
        result = minimize_window("telegram")
        assert result.success is True
        win.minimize.assert_called_once()


class TestRestoreWindow:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_calls_restore(self, mock_get_all):
        win = _make_win("Google Chrome")
        mock_get_all.return_value = [win]
        result = restore_window("chrome")
        assert result.success is True
        win.restore.assert_called_once()


class TestListWindows:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_filters_and_dedupes(self, mock_get_all):
        mock_get_all.return_value = [
            _make_win("Google Chrome"),
            _make_win("Google Chrome"),
            _make_win("A"),
            _make_win("Program Manager"),
            _make_win("Telegram Desktop"),
        ]
        result = list_windows()
        assert result == ["Google Chrome", "Telegram Desktop"]

    @patch("managers.window_manager.gw.getAllWindows")
    def test_empty_when_all_filtered(self, mock_get_all):
        mock_get_all.return_value = [_make_win("Program Manager"), _make_win("A")]
        assert list_windows() == []


class TestGetActiveWindow:
    @patch("managers.window_manager.psutil.Process")
    @patch("managers.window_manager.win32process")
    @patch("managers.window_manager.gw.getActiveWindow")
    def test_happy_path(self, mock_active, mock_win32, mock_process):
        win = _make_win("Visual Studio Code", 555)
        mock_active.return_value = win
        mock_win32.GetWindowThreadProcessId.return_value = (0, 42)
        mock_process.return_value.name.return_value = "Code.exe"

        result = get_active_window()
        assert result.success is True
        assert result.matched_title == "Visual Studio Code"
        assert result.handle == 555
        assert result.process_name == "Code.exe"

    @patch("managers.window_manager.gw.getActiveWindow")
    def test_no_active_window(self, mock_active):
        mock_active.return_value = None
        result = get_active_window()
        assert result.success is True
        assert result.matched_title is None


class TestSingleEnumeration:
    @patch("managers.window_manager.gw.getAllWindows")
    def test_focus_calls_get_all_windows_once(self, mock_get_all):
        win = _make_win("Google Chrome")
        mock_get_all.return_value = [win]
        focus_window("chrome")
        mock_get_all.assert_called_once()

    @patch("managers.window_manager.gw.getAllWindows")
    def test_maximize_calls_get_all_windows_once(self, mock_get_all):
        win = _make_win("Google Chrome")
        mock_get_all.return_value = [win]
        maximize_window("chrome")
        mock_get_all.assert_called_once()
