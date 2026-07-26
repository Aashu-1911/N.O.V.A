from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class CapabilityResponse:
    """Standardized response structure returned by every subsystem capability."""
    status: str
    reply: str
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    handled_by: str = ""
    verification_result: Optional[bool] = None
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    context_updates: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert standard response to dictionary representation for backward compatibility."""
        return {
            "status": self.status,
            "reply": self.reply,
            "payload": self.payload,
            "confidence": self.confidence,
            "handled_by": self.handled_by,
            "verification_result": self.verification_result,
            "execution_time": self.execution_time,
            "errors": self.errors,
            "warnings": self.warnings,
            "context_updates": self.context_updates,
        }
