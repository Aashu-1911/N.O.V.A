from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from capabilities.response import CapabilityResponse

# ============================================================================
# Semantic Target / Reference Classes
# ============================================================================

class Reference:
    """Base class for all semantic target references."""
    pass

@dataclass
class ReferenceWrapper(Reference):
    """Fallback reference for raw string values."""
    value: str
    
    def __str__(self) -> str:
        return self.value

@dataclass
class PronounReference(Reference):
    pronoun: str

@dataclass
class WindowReference(Reference):
    window_name: str

@dataclass
class ApplicationReference(Reference):
    app_name: str

@dataclass
class ResolvedWindowTarget(Reference):
    hwnd: Optional[int]
    pid: int
    process_name: str
    application: str
    title: str
    error_code: Optional[str] = None

@dataclass
class BrowserReference(Reference):
    browser_name: str

@dataclass
class UIElementReference(Reference):
    element_name: str

@dataclass
class VisionTarget(Reference):
    target_name: str

@dataclass
class OCRTarget(Reference):
    target_name: str

@dataclass
class FileReference(Reference):
    file_path: str

@dataclass
class ClipboardReference(Reference):
    pass

@dataclass
class SelectionReference(Reference):
    pass

@dataclass
class CursorReference(Reference):
    pass

@dataclass
class TextBoxReference(Reference):
    pass

@dataclass
class PreviousWindowReference(Reference):
    pass

@dataclass
class TemporalReference(Reference):
    keyword: str

@dataclass
class FocusedReference(Reference):
    keyword: str

@dataclass
class LocationReference(Reference):
    keyword: str

@dataclass
class NeedsClarification(Reference):
    reply: str


# ============================================================================
# Command Representations
# ============================================================================

@dataclass
class ParsedCommand:
    """Lightweight representation of a semantically parsed user request."""
    raw_command: str
    verb: Optional[str] = None
    target: Optional[Reference] = None
    scope: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    direct_response: Optional[Dict[str, Any]] = None

    @property
    def object(self) -> Optional[str]:
        # Return string representation of target for backwards compatibility
        if self.target is None:
            return None
        if hasattr(self.target, "pronoun"):
            return self.target.pronoun
        if hasattr(self.target, "window_name"):
            return self.target.window_name
        if hasattr(self.target, "app_name"):
            return self.target.app_name
        if hasattr(self.target, "browser_name"):
            return self.target.browser_name
        if hasattr(self.target, "element_name"):
            return self.target.element_name
        if hasattr(self.target, "target_name"):
            return self.target.target_name
        if hasattr(self.target, "file_path"):
            return self.target.file_path
        if hasattr(self.target, "keyword"):
            return self.target.keyword
        if hasattr(self.target, "value"):
            return self.target.value
        return str(self.target)

    @object.setter
    def object(self, value: Optional[str]) -> None:
        if value is None:
            self.target = None
        else:
            self.target = ReferenceWrapper(value)

@dataclass
class ResolvedCommand(ParsedCommand):
    """Command representation after semantic reference resolution has occurred."""
    pass


# ============================================================================
# Base Capability Interface
# ============================================================================

class BaseCapability(ABC):
    """Abstract base class establishing the contract for all subsystem capabilities."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of the capability."""
        pass

    @abstractmethod
    def priority(self) -> int:
        """Defines the routing priority precedence (higher integer = higher priority)."""
        pass

    @property
    @abstractmethod
    def supported_verbs(self) -> List[str]:
        """Lists verbs this capability explicitly supports."""
        pass

    @property
    @abstractmethod
    def supported_objects(self) -> List[str]:
        """Lists objects this capability explicitly supports."""
        pass

    @abstractmethod
    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        """Calculates a match confidence score (from 0.0 to 1.0) for handling the request."""
        pass

    @abstractmethod
    def health(self) -> bool:
        """Self-diagnostics health check. Returns True if dependencies are available."""
        pass

    @abstractmethod
    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        """Executes the specific business logic and returns a standardized response."""
        pass
