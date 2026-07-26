from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand
from capabilities.response import CapabilityResponse

class OCRCapability(BaseCapability):
    """Placeholder capability representing screen text extraction (OCR) subsystem."""

    @property
    def name(self) -> str:
        return "OCRCapability"

    def priority(self) -> int:
        return 60

    @property
    def supported_verbs(self) -> List[str]:
        return ["read", "extract"]

    @property
    def supported_objects(self) -> List[str]:
        return ["text", "image", "invoice"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            # If extracting/reading text from an image/invoice
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0
            if "source" in parsed.entities:
                return 1.0

        # Direct string check fallback
        ocr_phrases = {"read text", "extract text", "read invoice", "read image"}
        raw_lower = parsed.raw_command.lower()
        if any(phrase in raw_lower for phrase in ocr_phrases):
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        interpretation = f"OCR semantic action: '{parsed.verb}' on source '{parsed.object}'"
        return CapabilityResponse(
            status="success",
            reply="OCR capability not implemented.",
            payload={
                "interpretation": interpretation,
                "execution_summary": "Skipped (OCR not implemented)"
            },
            verification_result=True
        )
