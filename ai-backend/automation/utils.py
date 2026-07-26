import win32gui
import win32process
import psutil
from typing import Optional

def is_hwnd_valid(hwnd: int) -> bool:
    """Check if the given window handle is a valid and visible window."""
    return bool(win32gui.IsWindow(hwnd))

def get_pid_from_hwnd(hwnd: int) -> Optional[int]:
    """Retrieve process ID associated with the window handle."""
    if not is_hwnd_valid(hwnd):
        return None
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception:
        return None

def get_process_name_from_hwnd(hwnd: int) -> Optional[str]:
    """Retrieve process name from window handle."""
    pid = get_pid_from_hwnd(hwnd)
    if pid is None:
        return None
    try:
        return psutil.Process(pid).name()
    except Exception:
        return None

def get_window_title(hwnd: int) -> str:
    """Retrieve window text title from handle."""
    if not is_hwnd_valid(hwnd):
        return ""
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""
