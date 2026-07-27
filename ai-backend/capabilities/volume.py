from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand, ReferenceWrapper
from capabilities.response import CapabilityResponse
from handlers.system_handler import handle_volume_control

class VolumeCapability(BaseCapability):
    """Subsystem capability representing OS audio volume level management."""

    @property
    def name(self) -> str:
        return "VolumeCapability"

    def priority(self) -> int:
        return 85

    @property
    def supported_verbs(self) -> List[str]:
        return ["increase", "decrease", "mute", "unmute", "volume"]

    @property
    def supported_objects(self) -> List[str]:
        return ["volume", "sound", "up", "down", "mute", "unmute"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0
            if "volume_action" in parsed.entities:
                return 1.0

        # String matching check
        volume_keywords = {"increase volume", "decrease volume", "mute volume", "unmute volume", "volume up", "volume down"}
        raw_lower = parsed.raw_command.lower()
        if any(phrase in raw_lower for phrase in volume_keywords):
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        target_name = parsed.object
        if isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value

        entities = dict(parsed.entities)
        
        # Populate volume action if missing
        if not entities.get("volume_action"):
            if parsed.verb == "increase":
                entities["volume_action"] = "up"
            elif parsed.verb == "decrease":
                entities["volume_action"] = "down"
            elif parsed.verb == "volume":
                if target_name and "up" in target_name.lower():
                    entities["volume_action"] = "up"
                elif target_name and "down" in target_name.lower():
                    entities["volume_action"] = "down"
                else:
                    entities["volume_action"] = target_name
            else:
                entities["volume_action"] = parsed.verb

        interpretation = f"Volume action: '{entities.get('volume_action')}'"
        res = handle_volume_control(entities, context)
        verification_result = (res.get("status") == "success")

        # Context updates on success
        context_updates = {}
        if verification_result:
            context_updates = {"last_volume_action": entities.get("volume_action")}

        return CapabilityResponse(
            status=res.get("status", "success"),
            reply=res.get("reply", ""),
            payload={
                "interpretation": interpretation,
                "execution_summary": res.get("reply", ""),
                **res.get("payload", {})
            },
            verification_result=verification_result,
            context_updates=context_updates
        )
