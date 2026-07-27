from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand, BrowserReference, ReferenceWrapper
from capabilities.response import CapabilityResponse
from handlers.browser_handler import handle_open_website, handle_search_web
from handlers.query_handler import handle_browser_back

class BrowserCapability(BaseCapability):
    """Subsystem capability representing browser navigation and searches."""

    @property
    def name(self) -> str:
        return "BrowserCapability"

    def priority(self) -> int:
        return 90

    @property
    def supported_verbs(self) -> List[str]:
        return ["open", "search", "go", "refresh"]

    @property
    def supported_objects(self) -> List[str]:
        return ["github", "python", "weather", "url", "website"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        # Avoid collisions with UI automation elements
        ui_keywords = {"button", "textbox", "checkbox", "click", "list controls"}
        words = set(parsed.raw_command.lower().split())
        if words.intersection(ui_keywords):
            return 0.0

        if isinstance(parsed.target, BrowserReference):
            return 1.0

        if parsed.verb == "search":
            return 1.0

        if parsed.verb == "open":
            obj_lower = (parsed.object or "").lower()
            if "." in obj_lower or "http" in obj_lower or obj_lower in {"github", "google", "wikipedia"}:
                return 1.0

        if parsed.verb == "go" and (parsed.object == "back" or (parsed.target and isinstance(parsed.target, BrowserReference))):
            return 1.0

        if parsed.verb == "refresh":
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        # Interpreter logic (map semantic parsed commands to legacy handler actions)
        target_name = parsed.object
        if isinstance(parsed.target, BrowserReference):
            target_name = parsed.target.browser_name
        elif isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value

        entities = dict(parsed.entities)
        
        # Default entities mappings if missing
        if parsed.verb == "open":
            if not entities.get("url") and target_name:
                entities["url"] = target_name if "://" in target_name else f"https://{target_name}"
        elif parsed.verb == "search":
            if not entities.get("search_query"):
                entities["search_query"] = target_name

        interpretation = f"Browser action: '{parsed.verb}' with target '{target_name or parsed.object}'"

        # Execute & Verify
        if parsed.verb == "open":
            res = handle_open_website(entities, context)
            url = entities.get("url", "")
            context_updates = {"current_browser": "Chrome", "current_url": url}
            verification_result = True
        elif parsed.verb == "search":
            res = handle_search_web(entities, context)
            query = entities.get("search_query", "")
            context_updates = {
                "last_search_query": query,
                "current_browser": "Chrome",
                "current_url": f"https://www.google.com/search?q={query.replace(' ', '+')}"
            }
            verification_result = True
        elif parsed.verb == "go" and (target_name == "back" or entities.get("navigation_direction") == "back"):
            res = handle_browser_back(entities, context)
            context_updates = {}
            verification_result = True
        elif parsed.verb == "refresh":
            res = {"status": "success", "reply": "Refreshing the page.", "payload": {"action": "refresh"}}
            context_updates = {}
            verification_result = True
        else:
            res = {"status": "error", "reply": "Unsupported browser action."}
            context_updates = {}
            verification_result = False

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
