import time
import win32gui
import ctypes

class WindowVerifier:
    """Verifies that visual state transitions complete successfully using polling retries."""
    
    def verify_focus(self, hwnd: int) -> bool:
        for _ in range(10):  # Poll every 20ms up to 200ms
            if win32gui.GetForegroundWindow() == hwnd:
                return True
            time.sleep(0.02)
        return False

    def verify_minimize(self, hwnd: int) -> bool:
        for _ in range(10):
            if win32gui.IsIconic(hwnd):
                return True
            time.sleep(0.02)
        return False

    def verify_maximize(self, hwnd: int) -> bool:
        for _ in range(10):
            if ctypes.windll.user32.IsZoomed(hwnd):
                return True
            time.sleep(0.02)
        return False

    def verify_restore(self, hwnd: int) -> bool:
        for _ in range(10):
            # Must be visible and not iconic/zoomed (or just not iconic)
            if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                return True
            time.sleep(0.02)
        return False
