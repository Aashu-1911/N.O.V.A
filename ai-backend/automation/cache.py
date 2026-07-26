import threading
from typing import Dict, Any, Optional
import uiautomation as auto
from automation.utils import is_hwnd_valid

class AutomationCache:
    """Thread-safe intelligent caching system for windows, elements, and parent nodes."""
    
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._windows: Dict[str, int] = {}
        self._elements: Dict[str, Any] = {}
        self._parent_nodes: Dict[str, Any] = {}

    def cache_window(self, name: str, hwnd: int) -> None:
        """Cache window handle by identifier name."""
        with self._lock:
            self._windows[name] = hwnd

    def get_window(self, name: str) -> Optional[int]:
        """Retrieve valid cached window handle, invalidating automatically if invalid."""
        with self._lock:
            hwnd = self._windows.get(name)
            if hwnd is not None:
                if is_hwnd_valid(hwnd):
                    return hwnd
                self.invalidate_window(name)
            return None

    def cache_element(self, key: str, control: Any) -> None:
        """Cache UIA control element by search query key."""
        with self._lock:
            self._elements[key] = control

    def get_element(self, key: str) -> Optional[Any]:
        """Retrieve valid cached UIA control, invalidating automatically if invalid."""
        with self._lock:
            control = self._elements.get(key)
            if control is not None:
                if self.is_control_valid(control):
                    return control
                self.invalidate_element(key)
            return None

    def cache_parent(self, child_key: str, parent_control: Any) -> None:
        """Cache parent control reference."""
        with self._lock:
            self._parent_nodes[child_key] = parent_control

    def get_parent(self, child_key: str) -> Optional[Any]:
        """Retrieve cached parent reference, verifying validity."""
        with self._lock:
            control = self._parent_nodes.get(child_key)
            if control is not None:
                if self.is_control_valid(control):
                    return control
                self._parent_nodes.pop(child_key, None)
            return None

    def invalidate_window(self, name: str) -> None:
        """Remove window handle from cache."""
        with self._lock:
            self._windows.pop(name, None)

    def invalidate_element(self, key: str) -> None:
        """Remove element and its parent from caches."""
        with self._lock:
            self._elements.pop(key, None)
            self._parent_nodes.pop(key, None)

    def clear(self) -> None:
        """Clear all cache values."""
        with self._lock:
            self._windows.clear()
            self._elements.clear()
            self._parent_nodes.clear()

    @staticmethod
    def is_control_valid(control: Any) -> bool:
        """Verify if the COM pointer for a UIA element is still valid and active."""
        try:
            # Query NativeWindowHandle if available
            hwnd = getattr(control, "NativeWindowHandle", 0)
            if hwnd and not auto.IsWindow(hwnd):
                return False
            # Force COM property read to ensure runtime validity
            _ = control.Name
            return True
        except Exception:
            return False
