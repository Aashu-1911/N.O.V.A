"""
Window manager — OS-level window interaction via pygetwindow.

All operations return structured results and never raise exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import psutil
import pygetwindow as gw
from rapidfuzz import process

from utils.constants import SYSTEM_WINDOW_TITLES, WINDOW_MATCH_THRESHOLD

try:
    import win32process
except ImportError:
    win32process = None  # type: ignore[assignment]


@dataclass
class WindowOperationResult:
    success: bool
    matched_title: Optional[str] = None
    handle: Optional[int] = None
    reason: Optional[str] = None
    process_name: Optional[str] = None


def _find_window_obj(title: str):
    """Return the best-matching pygetwindow window object, or None."""
    try:
        all_windows = gw.getAllWindows()
    except Exception:
        return None

    candidates: dict[str, object] = {}
    for win in all_windows:
        t = win.title.strip()
        if len(t) >= 2 and t not in SYSTEM_WINDOW_TITLES:
            candidates[t] = win

    if not candidates:
        return None

    match = process.extractOne(
        title,
        list(candidates.keys()),
        score_cutoff=WINDOW_MATCH_THRESHOLD,
    )
    if match is None:
        return None

    return candidates[match[0]]


def _window_result_from_obj(win, success: bool = True, reason: Optional[str] = None) -> WindowOperationResult:
    handle = getattr(win, "_hWnd", None)
    return WindowOperationResult(
        success=success,
        matched_title=win.title if success else None,
        handle=handle,
        reason=reason,
    )


def focus_window(title: str) -> WindowOperationResult:
    try:
        win = _find_window_obj(title)
        if win is None:
            return WindowOperationResult(success=False, reason="Window not found")
        win.activate()
        return _window_result_from_obj(win)
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))


def maximize_window(title: str) -> WindowOperationResult:
    try:
        win = _find_window_obj(title)
        if win is None:
            return WindowOperationResult(success=False, reason="Window not found")
        win.maximize()
        return _window_result_from_obj(win)
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))


def minimize_window(title: str) -> WindowOperationResult:
    try:
        win = _find_window_obj(title)
        if win is None:
            return WindowOperationResult(success=False, reason="Window not found")
        win.minimize()
        return _window_result_from_obj(win)
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))


def restore_window(title: str) -> WindowOperationResult:
    try:
        win = _find_window_obj(title)
        if win is None:
            return WindowOperationResult(success=False, reason="Window not found")
        win.restore()
        return _window_result_from_obj(win)
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))


def list_windows() -> List[str]:
    try:
        all_windows = gw.getAllWindows()
    except Exception:
        return []

    candidates: dict[str, None] = {}
    for win in all_windows:
        t = win.title.strip()
        if len(t) >= 2 and t not in SYSTEM_WINDOW_TITLES:
            candidates[t] = None

    return sorted(candidates.keys())


def get_active_window() -> WindowOperationResult:
    try:
        win = gw.getActiveWindow()
        if win is None or not win.title.strip():
            return WindowOperationResult(success=True, matched_title=None)

        proc_name = None
        if win32process is not None:
            try:
                hwnd = win._hWnd
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                proc_name = psutil.Process(pid).name()
            except Exception:
                pass

        return WindowOperationResult(
            success=True,
            matched_title=win.title,
            handle=getattr(win, "_hWnd", None),
            process_name=proc_name,
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))
