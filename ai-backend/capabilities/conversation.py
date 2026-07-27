from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand, ReferenceWrapper
from capabilities.response import CapabilityResponse
from handlers.query_handler import handle_query_context

class ConversationCapability(BaseCapability):
    """Subsystem capability representing state-querying chat dialog."""

    @property
    def name(self) -> str:
        return "ConversationCapability"

    def priority(self) -> int:
        return 92

    @property
    def supported_verbs(self) -> List[str]:
        return ["query"]

    @property
    def supported_objects(self) -> List[str]:
        return ["current_application", "current_website", "last_opened_application"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        if parsed.verb in self.supported_verbs:
            if parsed.object in self.supported_objects:
                return 1.0
            if "query_type" in parsed.entities:
                return 1.0

        # Conversation questions checks
        conv_phrases = {"what did you open", "what website", "what application is open", "what app is open"}
        raw_lower = parsed.raw_command.lower()
        if any(phrase in raw_lower for phrase in conv_phrases):
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        target_name = parsed.object
        if isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value

        entities = dict(parsed.entities)
        
        # Populate query type
        if not entities.get("query_type"):
            entities["query_type"] = target_name

        interpretation = f"Conversation Context query: '{entities.get('query_type')}'"
        res = handle_query_context(entities, context)
        verification_result = (res.get("status") == "success")

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
