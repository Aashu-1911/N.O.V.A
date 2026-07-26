from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand
from capabilities.response import CapabilityResponse
from handlers.window_handler import handle_focus_window, handle_maximize_window, handle_minimize_window, handle_restore_window
from handlers.app_handler import handle_open_application, handle_close_application

class WindowCapability(BaseCapability):
    """Subsystem capability representing OS-level window and application management."""

    @property
    def name(self) -> str:
        return "WindowCapability"

    def priority(self) -> int:
        return 95

    @property
    def supported_verbs(self) -> List[str]:
        return ["open", "close", "focus", "maximize", "minimize", "restore", "list"]

    @property
    def supported_objects(self) -> List[str]:
        return ["application", "window", "app", "it", "notepad", "calculator", "chrome", "telegram"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()

        # Window/App management commands
        if parsed.verb in self.supported_verbs:
            # Avoid web URLs, which go to Browser
            if parsed.verb == "open" and ("." in obj_lower or "http" in obj_lower):
                return 0.0
            # Only handle list if targeting windows or apps
            if parsed.verb == "list" and "window" not in obj_lower and "app" not in obj_lower:
                return 0.0
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        # Interpreter mappings (do not map raw pronouns to names if unresolved)
        obj_clean = (parsed.object or "").strip()
        is_pronoun = obj_clean.lower() in {"it", "that", "this", "window", "app", "application", ""}
        
        entities = dict(parsed.entities)
        if not is_pronoun:
            if not entities.get("app_name"):
                entities["app_name"] = obj_clean
            if not entities.get("window_name"):
                entities["window_name"] = obj_clean
        else:
            if "app_name" not in entities:
                entities["app_name"] = None
            if "window_name" not in entities:
                entities["window_name"] = None

        interpretation = f"Window action: '{parsed.verb}' on application/window '{parsed.object}'"
        context_updates = {}
        verification_result = False

        if parsed.verb == "open":
            res = handle_open_application(entities, context)
            if res.get("status") == "success":
                app_name = entities.get("app_name", "").lower()
                context_updates = {
                    "current_application": app_name,
                    "current_window": app_name,
                    "last_opened_application": app_name
                }
                verification_result = True
        elif parsed.verb == "close":
            res = handle_close_application(entities, context)
            if res.get("status") == "success":
                app_name = entities.get("app_name", "").lower()
                context_updates = {
                    "current_application": None,
                    "current_window": None,
                    "last_closed_application": app_name
                }
                verification_result = True
        elif parsed.verb == "focus":
            res = handle_focus_window(entities, context)
            if res.get("status") == "success":
                win_name = entities.get("window_name", "")
                context_updates = {
                    "current_window": win_name,
                    "current_application": win_name
                }
                verification_result = True
        elif parsed.verb == "maximize":
            res = handle_maximize_window(entities, context)
            verification_result = (res.get("status") == "success")
            if verification_result:
                payload = res.get("payload") or {}
                context_updates = {
                    "last_window_operation": "maximize",
                    "current_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window_handle": payload.get("window_handle")
                }
        elif parsed.verb == "minimize":
            res = handle_minimize_window(entities, context)
            verification_result = (res.get("status") == "success")
            if verification_result:
                payload = res.get("payload") or {}
                context_updates = {
                    "last_window_operation": "minimize",
                    "current_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window_handle": payload.get("window_handle")
                }
        elif parsed.verb == "restore":
            res = handle_restore_window(entities, context)
            verification_result = (res.get("status") == "success")
            if verification_result:
                payload = res.get("payload") or {}
                context_updates = {
                    "last_window_operation": "restore",
                    "current_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window_handle": payload.get("window_handle")
                }
        else:
            res = {"status": "error", "reply": "Unsupported window management action."}

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
