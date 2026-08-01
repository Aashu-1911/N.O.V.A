import re
from typing import Any, Optional
from .snapshots import ContextSnapshot
from .dataclasses import (
    ResolvedWindow, ResolvedApplication, ResolvedBrowser, ResolvedFile,
    ResolvedClipboard, ResolvedTask, ResolvedPlanner, ResolvedConversation,
    ResolvedUI, ResolvedVision
)

class ContextResolver:
    """Intelligent layer resolving pronoun references and abstract terms to typed sub-contexts."""

    def resolve(self, expression: str, snapshot: ContextSnapshot) -> Any:
        expr_clean = expression.strip().lower()
        
        # 1. Pronouns
        if expr_clean in {"it", "this", "that"}:
            if snapshot.window.hwnd is not None:
                return snapshot.window
            if snapshot.application.name:
                return snapshot.application
            if snapshot.browser.url:
                return snapshot.browser
            if snapshot.file.current_file:
                return snapshot.file
            return snapshot.window
            
        # 2. Window keywords
        if expr_clean in {"window", "current window", "active window", "current"}:
            return snapshot.window

        # 3. Previous/last window keywords
        if expr_clean in {"previous window", "last window", "previous", "last"}:
            prev_hwnd = snapshot.window.previous_window
            if prev_hwnd:
                return ResolvedWindow(hwnd=prev_hwnd, title="Previous Window")
            return snapshot.window

        # 4. Browser keywords
        if expr_clean in {"browser", "current browser", "tab", "current tab"}:
            return snapshot.browser

        # 5. File keywords
        if expr_clean in {"folder", "directory", "current folder", "file", "current file"}:
            return snapshot.file

        # 6. Application keywords
        if expr_clean in {"application", "app", "current application", "current app"}:
            return snapshot.application

        # 7. Repeat/Same
        if expr_clean in {"same", "again"}:
            return snapshot.conversation

        # 8. Editor/Terminal
        if "editor" in expr_clean:
            return ResolvedApplication(name="VS Code", exec_path="code.exe")
        if "terminal" in expr_clean or "console" in expr_clean:
            return ResolvedApplication(name="PowerShell", exec_path="powershell.exe")

        # Fallback match
        if any(app in expr_clean for app in ["notepad", "calc", "calculator", "telegram", "vscode", "chrome"]):
            return ResolvedApplication(name=expression)

        return ResolvedWindow(title=expression)
