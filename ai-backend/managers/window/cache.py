import time
import ctypes
from ctypes import wintypes
import psutil
import win32gui
import win32con
import win32process
import win32api
from typing import List, Dict, Optional, Tuple, Any

from managers.window.model import WindowInfo
from utils.constants import SYSTEM_WINDOW_TITLES

class ProcessCache:
    """Caches process information (name, exe path, creation time) by PID to avoid slow calls."""
    def __init__(self) -> None:
        self._cache: Dict[int, Tuple[str, str, float]] = {}

    def get_process_info(self, pid: int) -> Tuple[str, str, float]:
        if pid in self._cache:
            return self._cache[pid]
        try:
            p = psutil.Process(pid)
            name = p.name()
            path = p.exe()
            ctime = p.create_time()
            self._cache[pid] = (name, path, ctime)
            return name, path, ctime
        except Exception:
            return "", "", 0.0

class WindowCache:
    """Retrieves and caches all running window properties, respecting cache TTL."""
    def __init__(self, process_cache: ProcessCache) -> None:
        self.process_cache = process_cache
        self._cached_windows: List[WindowInfo] = []
        self._last_update: float = 0.0
        self.ttl: float = 2.0  # 2 seconds cache duration

    def invalidate(self) -> None:
        self._last_update = 0.0

    def get_all_windows(self, force_refresh: bool = False) -> List[WindowInfo]:
        now = time.time()
        if not force_refresh and (now - self._last_update < self.ttl) and self._cached_windows:
            return self._cached_windows

        z_order_map: Dict[int, int] = {}
        
        def enum_cb(hwnd: int, extra: Any) -> bool:
            z_order_map[hwnd] = len(z_order_map)
            return True

        try:
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass

        dwmapi = ctypes.windll.dwmapi
        DWMWA_CLOAKED = 14
        windows: List[WindowInfo] = []

        for hwnd in z_order_map.keys():
            if not win32gui.IsWindow(hwnd):
                continue

            title = win32gui.GetWindowText(hwnd).strip()
            wclass = win32gui.GetClassName(hwnd)
            visible = bool(win32gui.IsWindowVisible(hwnd))

            # Fetch window dimensions
            try:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
            except Exception:
                width = height = 0

            # Detect if window is cloaked (hidden on another virtual desktop/suspended UWP app)
            cloaked = ctypes.c_int(0)
            hr = dwmapi.DwmGetWindowAttribute(
                wintypes.HWND(hwnd),
                DWMWA_CLOAKED,
                ctypes.byref(cloaked),
                ctypes.sizeof(cloaked)
            )
            is_cloaked = (cloaked.value != 0) if hr == 0 else False

            # Foreground and minimized/maximized state
            fore_hwnd = win32gui.GetForegroundWindow()
            is_foreground = (hwnd == fore_hwnd)
            is_minimized = bool(win32gui.IsIconic(hwnd))
            is_maximized = bool(ctypes.windll.user32.IsZoomed(hwnd))

            # Process attributes
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
            except Exception:
                pid = 0

            pname, ppath, pctime = ("", "", 0.0)
            if pid > 0:
                pname, ppath, pctime = self.process_cache.get_process_info(pid)

            # Monitor attributes
            try:
                monitor_h = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
                monitor_id = int(monitor_h)
            except Exception:
                monitor_id = 0

            z_order = z_order_map.get(hwnd, 9999)

            # Extract window capabilities based on styles
            capabilities = []
            try:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if style & win32con.WS_MINIMIZEBOX:
                    capabilities.append("minimize")
                if style & win32con.WS_MAXIMIZEBOX:
                    capabilities.append("maximize")
                if style & win32con.WS_THICKFRAME:
                    capabilities.append("resize")
                capabilities.append("close")
                capabilities.append("move")
            except Exception:
                pass

            win_info = WindowInfo(
                hwnd=hwnd,
                pid=pid,
                process_name=pname,
                executable_path=ppath,
                title=title,
                window_class=wclass,
                monitor=monitor_id,
                is_visible=visible,
                is_foreground=is_foreground,
                is_minimized=is_minimized,
                is_maximized=is_maximized,
                is_cloaked=is_cloaked,
                z_order=z_order,
                creation_time=pctime,
                capabilities=capabilities,
                width=width,
                height=height
            )
            windows.append(win_info)

        self._cached_windows = windows
        self._last_update = now
        return windows

def filter_standard_windows(windows: List[WindowInfo], include_hidden: bool = False) -> List[WindowInfo]:
    """Filters standard user-facing applications, ignoring helper/system ones."""
    filtered = []
    ignore_classes = {
        "Progman", "WorkerW", "Shell_TrayWnd", "Button", "Static",
        "IME", "MSCTFIME UI", "Windows.UI.Core.CoreWindow"
    }

    for w in windows:
        if not include_hidden:
            if not w.is_visible:
                continue
            if w.is_cloaked:
                continue
            if w.width <= 0 or w.height <= 0:
                continue
        
        # Check tool window style
        try:
            ex_style = win32gui.GetWindowLong(w.hwnd, win32con.GWL_EXSTYLE)
            if not include_hidden and (ex_style & win32con.WS_EX_TOOLWINDOW):
                continue
        except Exception:
            pass

        if w.window_class in ignore_classes:
            continue

        if not w.title or w.title in SYSTEM_WINDOW_TITLES:
            continue

        filtered.append(w)
    return filtered
