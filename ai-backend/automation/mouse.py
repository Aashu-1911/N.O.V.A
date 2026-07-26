import uiautomation as auto
import time

class Mouse:
    """Provides semantic mouse input controls using native Windows OS-level input events."""
    
    @staticmethod
    def click(x: int, y: int) -> None:
        """Move cursor to coordinate (x, y) and perform a left click."""
        auto.Click(x, y)

    @staticmethod
    def double_click(x: int, y: int) -> None:
        """Move cursor to coordinate (x, y) and perform a double left click."""
        auto.DoubleClick(x, y)

    @staticmethod
    def right_click(x: int, y: int) -> None:
        """Move cursor to coordinate (x, y) and perform a right click."""
        auto.RightClick(x, y)

    @staticmethod
    def hover(x: int, y: int, duration_sec: float = 0.1) -> None:
        """Move cursor to coordinate (x, y) and hover for a given duration."""
        auto.MoveTo(x, y)
        time.sleep(duration_sec)
