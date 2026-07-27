import time
from typing import List, Optional
from managers.window.model import WindowInfo

class WindowHistory:
    """Maintains active, previous, and historically focused windows."""
    def __init__(self) -> None:
        self.current_window: Optional[WindowInfo] = None
        self.previous_window: Optional[WindowInfo] = None
        self.recent_stack: List[int] = []  # Stack of window HWNDs
        self.current_hwnd: Optional[int] = None
        self.last_focus_time: float = 0.0
        self.last_operation: Optional[str] = None

    def record_focus(self, window_info: Optional[WindowInfo], operation: str = "focus") -> None:
        if not window_info:
            return

        if self.current_window and self.current_window.hwnd != window_info.hwnd:
            self.previous_window = self.current_window
            
        self.current_window = window_info
        self.current_hwnd = window_info.hwnd
        self.last_focus_time = time.time()
        self.last_operation = operation

        # Push to stack and prune duplicates/limit size
        if window_info.hwnd in self.recent_stack:
            self.recent_stack.remove(window_info.hwnd)
        self.recent_stack.append(window_info.hwnd)
        if len(self.recent_stack) > 50:
            self.recent_stack.pop(0)
