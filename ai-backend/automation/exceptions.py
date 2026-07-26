from typing import Optional

class AutomationError(Exception):
    """Base exception for all UI automation errors."""
    def __init__(
        self,
        action: str,
        target: str,
        reason: str,
        suggestions: Optional[str] = None
    ) -> None:
        self.action = action
        self.target = target
        self.reason = reason
        self.suggestions = suggestions
        msg = f"Action '{action}' on target '{target}' failed. Reason: {reason}."
        if suggestions:
            msg += f" Suggestions: {suggestions}"
        super().__init__(msg)


class WindowNotFoundError(AutomationError):
    """Raised when a target window cannot be located."""
    pass


class ElementNotFoundError(AutomationError):
    """Raised when a UI element matching criteria cannot be found."""
    pass


class ElementDisabledError(AutomationError):
    """Raised when an action is attempted on a disabled element."""
    pass


class ElementInvisibleError(AutomationError):
    """Raised when an action is attempted on an invisible element."""
    pass


class ActionTimeoutError(AutomationError):
    """Raised when an action or wait condition times out."""
    pass


class VerificationError(AutomationError):
    """Raised when post-action state verification fails."""
    pass


class AutomationUnavailableError(AutomationError):
    """Raised when standard Microsoft UIA services are unavailable."""
    pass
