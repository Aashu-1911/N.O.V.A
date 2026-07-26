from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand
from capabilities.response import CapabilityResponse
from handlers.media_handler import handle_play_music, handle_media_control

class MediaCapability(BaseCapability):
    """Subsystem capability representing media playback control."""

    @property
    def name(self) -> str:
        return "MediaCapability"

    def priority(self) -> int:
        return 85

    @property
    def supported_verbs(self) -> List[str]:
        return ["play", "pause", "skip", "stop", "media", "next", "previous", "resume"]

    @property
    def supported_objects(self) -> List[str]:
        return ["music", "song", "media", "track"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0
            if "media_action" in parsed.entities:
                return 1.0
            if parsed.verb == "resume" or parsed.verb == "pause":
                return 1.0

        # String matching check
        media_keywords = {"play music", "pause music", "pause song", "skip track", "pause", "next track", "previous track", "resume"}
        raw_lower = parsed.raw_command.lower()
        if any(phrase in raw_lower for phrase in media_keywords):
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        entities = dict(parsed.entities)
        
        # Determine intent to map to handlers
        intent = "media_control"
        if parsed.verb == "play":
            intent = "play_music"
            if not entities.get("media_query") and parsed.object:
                entities["media_query"] = parsed.object
        else:
            if not entities.get("media_action"):
                entities["media_action"] = parsed.verb

        interpretation = f"Media action: '{parsed.verb}' on query '{parsed.object}'"

        if intent == "play_music":
            res = handle_play_music(entities, context)
            verification_result = (res.get("status") == "success")
        elif intent == "media_control":
            res = handle_media_control(entities, context)
            verification_result = (res.get("status") == "success")
        else:
            res = {"status": "error", "reply": "Unsupported media action."}
            verification_result = False

        return CapabilityResponse(
            status=res.get("status", "success"),
            reply=res.get("reply", ""),
            payload={
                "interpretation": interpretation,
                "execution_summary": res.get("reply", ""),
                **res.get("payload", {})
            },
            verification_result=verification_result
        )
