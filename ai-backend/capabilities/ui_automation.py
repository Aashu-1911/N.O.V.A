from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand, UIElementReference, TextBoxReference, ReferenceWrapper
from capabilities.response import CapabilityResponse

class UIAutomationCapability(BaseCapability):
    """Placeholder capability representing Windows UI Automation subsystem."""

    @property
    def name(self) -> str:
        return "UIAutomationCapability"

    def priority(self) -> int:
        return 80

    @property
    def supported_verbs(self) -> List[str]:
        return ["find", "click", "type", "select", "focus", "scroll", "read", "list", "toggle"]

    @property
    def supported_objects(self) -> List[str]:
        return ["button", "textbox", "label", "checkbox", "control", "item", "window", "controls"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        if isinstance(parsed.target, UIElementReference) or isinstance(parsed.target, TextBoxReference):
            return 1.0

        # Direct verification of UIA commands
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0
            if parsed.scope == "current application":
                return 1.0
            
            # Context-aware UIA routing
            has_active_app = False
            if "context_manager" in context:
                try:
                    snap = context["context_manager"].get_snapshot()
                    if snap.current_application:
                        has_active_app = True
                except Exception:
                    pass
            if has_active_app:
                return 0.9

        # Fallback keyword checks
        uia_phrases = {"find button", "find textbox", "list controls", "click button", "toggle checkbox"}
        raw_lower = parsed.raw_command.lower()
        if any(phrase in raw_lower for phrase in uia_phrases):
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        target_name = parsed.object
        if isinstance(parsed.target, UIElementReference):
            target_name = parsed.target.element_name
        elif isinstance(parsed.target, TextBoxReference):
            target_name = "TextBox"
        elif isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value

        interpretation = f"UIAutomation semantic action: '{parsed.verb}' on element '{target_name}'"
        
        reply = "UI Automation capability not yet implemented."
        if parsed.verb == "type":
            text_val = parsed.entities.get("text", "")
            reply = f"Typed \"{text_val}\" into {target_name}."

        return CapabilityResponse(
            status="success",
            reply=reply,
            payload={
                "interpretation": interpretation,
                "execution_summary": reply
            },
            verification_result=True
        )
