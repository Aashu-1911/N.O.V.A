"""Unit tests for the new modular window manager and legacy compatibility APIs."""

import sys
import os
import time
import pytest
import ctypes
from unittest.mock import MagicMock, patch

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from managers.window.model import WindowInfo
from managers.window.errors import WindowError
from managers.window.matcher import WindowMatcher
from managers.window.resolver import WindowResolver
from managers.window.cache import WindowCache, ProcessCache
from managers.window.history import WindowHistory
from managers.window.manager import WindowManager
from managers.window_manager import (
    focus_window, maximize_window, minimize_window, restore_window, list_windows, get_active_window
)

class MockWindow:
    def __init__(self, hwnd, title, wclass, visible=True, rect=(100, 100, 900, 700), is_min=False, is_max=False, is_cloaked=False, pid=1234, pname="notepad.exe"):
        self.hwnd = hwnd
        self.title = title
        self.wclass = wclass
        self.visible = visible
        self.rect = rect
        self.is_min = is_min
        self.is_max = is_max
        self.is_cloaked = is_cloaked
        self.pid = pid
        self.pname = pname

@pytest.fixture
def win32_mock():
    # Setup mock windows
    mock_windows = [
        MockWindow(1001, "Notepad - document.txt", "Notepad", pname="notepad.exe"),
        MockWindow(1002, "OneNote - Personal Notebook", "Framework::CFrame", pname="onenote.exe"),
        MockWindow(1003, "Sticky Notes", "StickyCharWindow", pname="stickynotes.exe"),
        MockWindow(1004, "Google Chrome", "Chrome_WidgetWin_1", pname="chrome.exe"),
        MockWindow(1005, "", "HelperClass", visible=False, pname="helper.exe"), # invisible, no title
        MockWindow(1006, "Zero Sized Window", "ZeroClass", rect=(100, 100, 100, 100), pname="zero.exe") # zero-sized
    ]
    
    def enum_cb(callback, extra):
        for w in mock_windows:
            callback(w.hwnd, extra)
        return True

    def is_window(hwnd):
        return any(w.hwnd == hwnd for w in mock_windows)

    def get_window_text(hwnd):
        for w in mock_windows:
            if w.hwnd == hwnd:
                return w.title
        return ""

    def get_class_name(hwnd):
        for w in mock_windows:
            if w.hwnd == hwnd:
                return w.wclass
        return ""

    def is_window_visible(hwnd):
        for w in mock_windows:
            if w.hwnd == hwnd:
                return w.visible
        return False

    def get_window_rect(hwnd):
        for w in mock_windows:
            if w.hwnd == hwnd:
                return w.rect
        raise RuntimeError("Window not found")

    def is_iconic(hwnd):
        for w in mock_windows:
            if w.hwnd == hwnd:
                return w.is_min
        return False

    def is_zoomed(hwnd):
        for w in mock_windows:
            if w.hwnd == hwnd:
                return w.is_max
        return False

    with patch("win32gui.EnumWindows", side_effect=enum_cb), \
         patch("win32gui.IsWindow", side_effect=is_window), \
         patch("win32gui.GetWindowText", side_effect=get_window_text), \
         patch("win32gui.GetClassName", side_effect=get_class_name), \
         patch("win32gui.IsWindowVisible", side_effect=is_window_visible), \
         patch("win32gui.GetWindowRect", side_effect=get_window_rect), \
         patch("win32gui.IsIconic", side_effect=is_iconic), \
         patch("ctypes.windll.user32.IsZoomed", side_effect=is_zoomed), \
         patch("win32process.GetWindowThreadProcessId", return_value=(0, 1234)), \
         patch("win32api.MonitorFromWindow", return_value=9999), \
         patch("win32gui.GetWindowLong", return_value=0), \
         patch("win32gui.GetForegroundWindow", return_value=1001), \
         patch("psutil.Process") as mock_proc:
         
         # Configure psutil mock
         proc_instance = MagicMock()
         proc_instance.name.return_value = "notepad.exe"
         proc_instance.exe.return_value = "C:\\Windows\\notepad.exe"
         proc_instance.create_time.return_value = 12345.67
         mock_proc.return_value = proc_instance
         
         yield mock_windows

def test_matcher_scoring():
    matcher = WindowMatcher()
    
    # 1. Notepad Match
    win_notepad = WindowInfo(
        hwnd=1001, pid=1234, process_name="notepad.exe", executable_path="path",
        title="Notepad - document.txt", window_class="Notepad", monitor=1,
        is_visible=True, is_foreground=False, is_minimized=False, is_maximized=False,
        is_cloaked=False, z_order=0, creation_time=0.0, capabilities=[]
    )
    assert matcher.score(win_notepad, "note") == 1.0

    # 2. OneNote Match
    win_onenote = WindowInfo(
        hwnd=1002, pid=1234, process_name="onenote.exe", executable_path="path",
        title="OneNote - Personal Notebook", window_class="Framework", monitor=1,
        is_visible=True, is_foreground=False, is_minimized=False, is_maximized=False,
        is_cloaked=False, z_order=1, creation_time=0.0, capabilities=[]
    )
    assert matcher.score(win_onenote, "note") == 0.72

    # 3. Sticky Notes Match
    win_sticky = WindowInfo(
        hwnd=1003, pid=1234, process_name="stickynotes.exe", executable_path="path",
        title="Sticky Notes", window_class="StickyCharWindow", monitor=1,
        is_visible=True, is_foreground=False, is_minimized=False, is_maximized=False,
        is_cloaked=False, z_order=2, creation_time=0.0, capabilities=[]
    )
    assert matcher.score(win_sticky, "note") == 0.45

def test_filtering_and_cache(win32_mock):
    p_cache = ProcessCache()
    w_cache = WindowCache(p_cache)
    
    windows = w_cache.get_all_windows()
    # 6 windows total in mock
    assert len(windows) == 6
    
    # Cache hit check
    windows_again = w_cache.get_all_windows()
    assert len(windows_again) == 6

    from managers.window.cache import filter_standard_windows
    filtered = filter_standard_windows(windows)
    # notepad, onenote, sticky notes, google chrome remain (4 windows)
    # Invisible and zero-sized should be ignored
    assert len(filtered) == 4

def test_resolver_selection(win32_mock):
    p_cache = ProcessCache()
    w_cache = WindowCache(p_cache)
    matcher = WindowMatcher()
    history = WindowHistory()
    resolver = WindowResolver(w_cache, matcher, history)

    # Resolve "note" -> Notepad has 1.0, OneNote has 0.72, Sticky Notes has 0.45
    chosen, scored, err = resolver.choose_best_window("note")
    assert err is None
    assert chosen.title == "Notepad - document.txt"

def test_focus_already_focused_no_op(win32_mock):
    # Setup manager
    manager = WindowManager()
    
    # Notepad is Mock HWND 1001. Current Foreground Mock returns 1001.
    with patch("win32gui.GetForegroundWindow", return_value=1001):
        success, win_info, err = manager.focus_window("Notepad")
        assert success is True
        assert win_info.hwnd == 1001
        assert err is None

def test_focus_non_existent_window(win32_mock):
    manager = WindowManager()
    success, win_info, err = manager.focus_window("nonexistent_app_name")
    assert success is False
    assert err == "WINDOW_NOT_FOUND"

@patch("win32gui.SetForegroundWindow", return_value=True)
@patch("win32gui.BringWindowToTop", return_value=True)
def test_activator_pipeline(mock_top, mock_fg, win32_mock):
    manager = WindowManager()
    # Mocking foreground check to return destination HWND to simulate success
    with patch("win32gui.GetForegroundWindow", return_value=1004):
        success, win_info, err = manager.focus_window("chrome")
        assert success is True
        assert win_info.hwnd == 1004
        assert err is None

def test_legacy_api_compatibility(win32_mock):
    # Verify legacy focus_window exports wrapper correctly
    with patch("win32gui.GetForegroundWindow", return_value=1001):
        res = focus_window("Notepad")
        assert res.success is True
        assert res.handle == 1001
        assert res.matched_title == "Notepad - document.txt"

    # Verify list_windows returns unique titles
    titles = list_windows()
    assert "Notepad - document.txt" in titles
    assert "Google Chrome" in titles

def test_punctuation_normalization_parser():
    from capabilities.parser import CommandParser
    from capabilities.base import WindowReference
    
    p1 = CommandParser.parse("Focus notepad.")
    assert isinstance(p1.target, WindowReference)
    assert p1.target.window_name == "notepad"
    
    p2 = CommandParser.parse("Focus notepad,")
    assert p2.target.window_name == "notepad"
    
    p3 = CommandParser.parse('Focus "notepad"')
    assert p3.target.window_name == "notepad"
    
    p4 = CommandParser.parse("Focus (notepad)")
    assert p4.target.window_name == "notepad"
    
    p5 = CommandParser.parse("Focus notepad?")
    assert p5.target.window_name == "notepad"

def test_whisper_variants_matching(win32_mock):
    manager = WindowManager()
    
    with patch("win32gui.GetForegroundWindow", return_value=1001):
        success, win, err = manager.focus_window("note pad")
        assert success is True
        assert win.hwnd == 1001

        success, win, err = manager.focus_window("NotePad")
        assert success is True
        assert win.hwnd == 1001

        success, win, err = manager.focus_window("note-pad")
        assert success is True
        assert win.hwnd == 1001

def test_failure_recovery_codes(win32_mock):
    manager = WindowManager()
    
    # 1. Non-existent window
    success, win, err = manager.focus_window("Photoshop")
    assert success is False
    assert err == "WINDOW_NOT_FOUND"
    
    # 2. Close already closed window
    success, win, err = manager.close_window("Photoshop")
    assert success is False
    assert err == "WINDOW_ALREADY_CLOSED"

    # 3. Destroyed HWND query
    with patch("win32gui.IsWindow", return_value=False):
        success, win, err = manager.focus_window("9999")
        assert success is False
        assert err == "WINDOW_DESTROYED"

