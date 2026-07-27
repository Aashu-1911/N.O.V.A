from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand, VisionTarget
from capabilities.response import CapabilityResponse

class VisionCapability(BaseCapability):
    """Placeholder capability representing screen Vision subsystem."""

    @property
    def name(self) -> str:
        return "VisionCapability"

    def priority(self) -> int:
        return 70

    @property
    def supported_verbs(self) -> List[str]:
        return ["describe", "look", "observe", "read", "locate"]

    @property
    def supported_objects(self) -> List[str]:
        return ["screen", "popup", "icon", "image"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        if isinstance(parsed.target, VisionTarget):
            return 1.0

        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0

        # Match specific phrases
        vision_phrases = {"describe screen", "what's on my screen", "read popup", "locate icon", "observe screen", "read screen"}
        raw_lower = parsed.raw_command.lower()
        if any(phrase in raw_lower for phrase in vision_phrases):
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        interpretation = f"Vision semantic action: '{parsed.verb}' on target '{parsed.object}'"
        reply = "Vision Result: Captured Screen analysis shows an open window." if isinstance(parsed.target, VisionTarget) else "Vision capability not implemented."
        return CapabilityResponse(
            status="success",
            reply=reply,
            payload={
                "interpretation": interpretation,
                "execution_summary": reply
            },
            verification_result=True
        )
