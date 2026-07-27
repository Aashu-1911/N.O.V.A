import time
import logging
import win32gui
import win32con
from typing import List, Optional, Dict, Any, Tuple

from managers.window.model import WindowInfo
from managers.window.errors import WindowError
from managers.window.cache import ProcessCache, WindowCache, filter_standard_windows
from managers.window.matcher import WindowMatcher
from managers.window.resolver import WindowResolver
from managers.window.activator import WindowActivator
from managers.window.verifier import WindowVerifier
from managers.window.history import WindowHistory

logger = logging.getLogger("N.O.V.A.WindowManager")

class WindowManager:
    """Unified coordinator for system window discovery, state mutation, history and activation."""
    def __init__(self) -> None:
        self.process_cache = ProcessCache()
        self.cache = WindowCache(self.process_cache)
        self.matcher = WindowMatcher()
        self.history = WindowHistory()
        self.resolver = WindowResolver(self.cache, self.matcher, self.history)
        self.activator = WindowActivator()
        self.verifier = WindowVerifier()

    def _log_operation(self, operation: str, query: str, start_time: float, 
                       candidates: List[Tuple[WindowInfo, float]], 
                       chosen: Optional[WindowInfo], api_calls: List[str], 
                       success: bool, reason: Optional[str]) -> None:
        elapsed = (time.time() - start_time) * 1000.0
        log_lines = [
            f"=== Window Operation: {operation.upper()} ===",
            f"Query:          '{query}'",
            f"Candidates:     {[(w.title, round(s, 2)) for w, s in candidates]}",
            f"Chosen Window:  '{chosen.title if chosen else 'None'}'",
            f"HWND:           {chosen.hwnd if chosen else 'None'}",
            f"Current State:  min={chosen.is_minimized if chosen else False}, max={chosen.is_maximized if chosen else False}, vis={chosen.is_visible if chosen else False}",
            f"Win32 API:      {api_calls}",
            f"Verification:   {'Successful' if success else 'Failed (' + (reason or 'unknown') + ')'}",
            f"Elapsed Time:   {elapsed:.2f} ms",
            "=========================================="
        ]
        log_str = "\n".join(log_lines)
        logger.info(log_str)
        print(log_str, flush=True)

    def get_window_info(self, query: str) -> Tuple[Optional[WindowInfo], List[Tuple[WindowInfo, float]], Optional[str]]:
        """Resolves the query to a WindowInfo object."""
        # Make sure cache has fresh enumeration
        self.cache.get_all_windows(force_refresh=True)
        return self.resolver.choose_best_window(query)

    def focus_window(self, query: str) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        api_calls = []
        
        # Check if query is already active to detect no-op
        active_hwnd = win32gui.GetForegroundWindow()
        if active_hwnd:
            self.cache.get_all_windows(force_refresh=True)
            for w in self.cache._cached_windows:
                if w.hwnd == active_hwnd:
                    # Score it
                    score = self.matcher.score(w, query)
                    if score >= 1.0: # Exact or perfect match
                        self.history.record_focus(w, "focus")
                        self._log_operation("focus", query, t0, [(w, score)], w, ["GetForegroundWindow (no-op)"], True, None)
                        return True, w, None

        chosen, scored, err = self.resolver.choose_best_window(query)
        if err:
            self._log_operation("focus", query, t0, scored, None, [], False, err)
            return False, None, err

        api_calls.append("ResolveWindow")
        
        # Activate window
        success, act_err = self.activator.activate(chosen.hwnd)
        api_calls.append("ShowWindow/BringWindowToTop/SetForegroundWindow")
        if not success:
            self._log_operation("focus", query, t0, scored, chosen, api_calls, False, act_err)
            return False, chosen, act_err

        # Verify
        verified = self.verifier.verify_focus(chosen.hwnd)
        api_calls.append("VerifyFocus")
        if not verified:
            self._log_operation("focus", query, t0, scored, chosen, api_calls, False, "FOREGROUND_RESTRICTED")
            return False, chosen, "FOREGROUND_RESTRICTED"

        # Record focus
        self.history.record_focus(chosen, "focus")
        self.cache.invalidate()
        self._log_operation("focus", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def maximize_window(self, query: str) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        chosen, scored, err = self.get_window_info(query)
        if err:
            self._log_operation("maximize", query, t0, scored, None, [], False, err)
            return False, None, err

        api_calls = ["ShowWindow(SW_MAXIMIZE)"]
        try:
            win32gui.ShowWindow(chosen.hwnd, win32con.SW_MAXIMIZE)
        except Exception as e:
            self._log_operation("maximize", query, t0, scored, chosen, api_calls, False, str(e))
            return False, chosen, "ACCESS_DENIED"

        verified = self.verifier.verify_maximize(chosen.hwnd)
        api_calls.append("VerifyMaximize")
        if not verified:
            self._log_operation("maximize", query, t0, scored, chosen, api_calls, False, "STATE_MUTATION_FAILED")
            return False, chosen, "STATE_MUTATION_FAILED"

        self.cache.invalidate()
        self._log_operation("maximize", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def minimize_window(self, query: str) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        chosen, scored, err = self.get_window_info(query)
        if err:
            self._log_operation("minimize", query, t0, scored, None, [], False, err)
            return False, None, err

        api_calls = ["ShowWindow(SW_MINIMIZE)"]
        try:
            win32gui.ShowWindow(chosen.hwnd, win32con.SW_MINIMIZE)
        except Exception as e:
            self._log_operation("minimize", query, t0, scored, chosen, api_calls, False, str(e))
            return False, chosen, "ACCESS_DENIED"

        verified = self.verifier.verify_minimize(chosen.hwnd)
        api_calls.append("VerifyMinimize")
        if not verified:
            self._log_operation("minimize", query, t0, scored, chosen, api_calls, False, "STATE_MUTATION_FAILED")
            return False, chosen, "STATE_MUTATION_FAILED"

        self.cache.invalidate()
        self._log_operation("minimize", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def restore_window(self, query: str) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        chosen, scored, err = self.get_window_info(query)
        if err:
            self._log_operation("restore", query, t0, scored, None, [], False, err)
            return False, None, err

        api_calls = ["ShowWindow(SW_RESTORE)"]
        try:
            win32gui.ShowWindow(chosen.hwnd, win32con.SW_RESTORE)
        except Exception as e:
            self._log_operation("restore", query, t0, scored, chosen, api_calls, False, str(e))
            return False, chosen, "ACCESS_DENIED"

        verified = self.verifier.verify_restore(chosen.hwnd)
        api_calls.append("VerifyRestore")
        if not verified:
            self._log_operation("restore", query, t0, scored, chosen, api_calls, False, "STATE_MUTATION_FAILED")
            return False, chosen, "STATE_MUTATION_FAILED"

        self.cache.invalidate()
        self._log_operation("restore", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def toggle_minimize(self, query: str) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        chosen, scored, err = self.get_window_info(query)
        if err:
            return False, None, err
        if chosen.is_minimized:
            return self.restore_window(query)
        else:
            return self.minimize_window(query)

    def close_window(self, query: str) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        chosen, scored, err = self.get_window_info(query)
        if err:
            err_code = "WINDOW_ALREADY_CLOSED" if err == "WINDOW_NOT_FOUND" else err
            self._log_operation("close", query, t0, scored, None, [], False, err_code)
            return False, None, err_code

        api_calls = ["PostMessage(WM_CLOSE)"]
        try:
            win32gui.PostMessage(chosen.hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception as e:
            self._log_operation("close", query, t0, scored, chosen, api_calls, False, str(e))
            return False, chosen, "ACCESS_DENIED"

        # Verify window is closed
        success = False
        for _ in range(10):
            if not win32gui.IsWindow(chosen.hwnd):
                success = True
                break
            time.sleep(0.05)

        api_calls.append("VerifyDestroyed")
        if not success:
            self._log_operation("close", query, t0, scored, chosen, api_calls, False, "STATE_MUTATION_FAILED")
            return False, chosen, "STATE_MUTATION_FAILED"

        self.cache.invalidate()
        self._log_operation("close", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def move_window(self, query: str, x: int, y: int, width: int, height: int) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        chosen, scored, err = self.get_window_info(query)
        if err:
            return False, None, err
        api_calls = ["SetWindowPos"]
        try:
            win32gui.SetWindowPos(chosen.hwnd, 0, x, y, width, height, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
        except Exception as e:
            self._log_operation("move", query, t0, scored, chosen, api_calls, False, str(e))
            return False, chosen, "ACCESS_DENIED"
        
        self.cache.invalidate()
        self._log_operation("move", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def resize_window(self, query: str, width: int, height: int) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        t0 = time.time()
        chosen, scored, err = self.get_window_info(query)
        if err:
            return False, None, err
        api_calls = ["SetWindowPos"]
        try:
            # Keep original X and Y
            rect = win32gui.GetWindowRect(chosen.hwnd)
            x, y = rect[0], rect[1]
            win32gui.SetWindowPos(chosen.hwnd, 0, x, y, width, height, win32con.SWP_NOZORDER | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE)
        except Exception as e:
            self._log_operation("resize", query, t0, scored, chosen, api_calls, False, str(e))
            return False, chosen, "ACCESS_DENIED"
        
        self.cache.invalidate()
        self._log_operation("resize", query, t0, scored, chosen, api_calls, True, None)
        return True, chosen, None

    def list_windows(self) -> List[str]:
        self.cache.get_all_windows(force_refresh=True)
        filtered = filter_standard_windows(self.cache._cached_windows)
        titles = sorted(list({w.title for w in filtered if w.title}))
        return titles

    def get_active_window(self) -> Tuple[bool, Optional[WindowInfo], Optional[str]]:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return True, None, None
        
        self.cache.get_all_windows(force_refresh=True)
        for w in self.cache._cached_windows:
            if w.hwnd == hwnd:
                return True, w, None
                
        # If not in cache, resolve standard attributes directly
        # E.g. get wclass, title, pid, etc.
        try:
            import win32process
            import win32api
            title = win32gui.GetWindowText(hwnd)
            wclass = win32gui.GetClassName(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            pname, ppath, pctime = self.process_cache.get_process_info(pid)
            win_info = WindowInfo(
                hwnd=hwnd, pid=pid, process_name=pname, executable_path=ppath,
                title=title, window_class=wclass, monitor=0, is_visible=True,
                is_foreground=True, is_minimized=False, is_maximized=False,
                is_cloaked=False, z_order=0, creation_time=pctime, capabilities=[]
            )
            return True, win_info, None
        except Exception as e:
            return False, None, str(e)
