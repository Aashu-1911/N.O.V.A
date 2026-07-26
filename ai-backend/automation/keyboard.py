import uiautomation as auto
import time
from typing import List

class Keyboard:
    """Provides semantic keyboard input controls using native OS-level key events."""
    
    @staticmethod
    def type_text(text: str, interval: float = 0.01) -> None:
        """Types the given text sequence with an optional typing interval."""
        # Escape braces for uiautomation SendKeys parser
        escaped = []
        for char in text:
            if char == "{":
                escaped.append("{{}")
            elif char == "}":
                escaped.append("{}}")
            else:
                escaped.append(char)
        escaped_str = "".join(escaped)
        auto.SendKeys(escaped_str, interval=interval)

    @staticmethod
    def press_enter() -> None:
        """Simulate pressing the Enter key."""
        auto.SendKeys("{Enter}")

    @staticmethod
    def press_escape() -> None:
        """Simulate pressing the Escape key."""
        auto.SendKeys("{Esc}")

    @staticmethod
    def press_tab() -> None:
        """Simulate pressing the Tab key."""
        auto.SendKeys("{Tab}")

    @staticmethod
    def send_shortcut(keys: str) -> None:
        """Send a keyboard shortcut combination (e.g. '{Ctrl}a', '{Ctrl}c')."""
        auto.SendKeys(keys)
