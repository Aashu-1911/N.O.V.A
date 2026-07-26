import pyperclip
from typing import Optional

class Clipboard:
    """Utility class to read/write from/to the Windows clipboard."""
    
    @staticmethod
    def set_text(text: str) -> None:
        """Copy text to clipboard."""
        pyperclip.copy(text)

    @staticmethod
    def get_text() -> str:
        """Get text from clipboard."""
        return pyperclip.paste()

    @staticmethod
    def clear() -> None:
        """Clear clipboard contents."""
        pyperclip.copy("")
