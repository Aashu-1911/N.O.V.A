from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from capabilities.response import CapabilityResponse

@dataclass
class ParsedCommand:
    """Lightweight representation of a semantically parsed user request."""
    raw_command: str
    verb: Optional[str] = None
    object: Optional[str] = None
    scope: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    direct_response: Optional[Dict[str, Any]] = None

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
