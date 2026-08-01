from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from managers.window import WindowManager, WindowInfo

@dataclass
class WindowOperationResult:
    success: bool
    matched_title: Optional[str] = None
    handle: Optional[int] = None
    reason: Optional[str] = None
    process_name: Optional[str] = None
    error_code: Optional[str] = None
    state: Optional[str] = None

# Singleton instance of the new hardened WindowManager
_manager = WindowManager()

def focus_window(title: str) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.focus_window(title)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def maximize_window(title: str) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.maximize_window(title)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def minimize_window(title: str) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.minimize_window(title)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def restore_window(title: str) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.restore_window(title)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def list_windows() -> List[str]:
    try:
        return _manager.list_windows()
    except Exception:
        return []

def get_active_window() -> WindowOperationResult:
    try:
        success, win_info, err = _manager.get_active_window()
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def toggle_minimize(title: str) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.toggle_minimize(title)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def close_window(title: str) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.close_window(title)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def move_window(title: str, x: int, y: int, width: int, height: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.move_window(title, x, y, width, height)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def resize_window(title: str, width: int, height: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.resize_window(title, width, height)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def focus_window_by_hwnd(hwnd: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.focus_window_by_hwnd(hwnd)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def maximize_window_by_hwnd(hwnd: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.maximize_window_by_hwnd(hwnd)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def minimize_window_by_hwnd(hwnd: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.minimize_window_by_hwnd(hwnd)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def restore_window_by_hwnd(hwnd: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.restore_window_by_hwnd(hwnd)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            process_name=win_info.process_name if win_info else None,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e), error_code="ACCESS_DENIED")

def toggle_minimize_by_hwnd(hwnd: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.toggle_minimize_by_hwnd(hwnd)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def close_window_by_hwnd(hwnd: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.close_window_by_hwnd(hwnd)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def move_window_by_hwnd(hwnd: int, x: int, y: int, width: int, height: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.move_window_by_hwnd(hwnd, x, y, width, height)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))

def resize_window_by_hwnd(hwnd: int, width: int, height: int) -> WindowOperationResult:
    try:
        success, win_info, err = _manager.resize_window_by_hwnd(hwnd, width, height)
        return WindowOperationResult(
            success=success,
            matched_title=win_info.title if win_info else None,
            handle=win_info.hwnd if win_info else None,
            reason=err,
            error_code=err
        )
    except Exception as e:
        return WindowOperationResult(success=False, reason=str(e))
