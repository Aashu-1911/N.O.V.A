from typing import Any, Dict, List
from capabilities.base import (
    BaseCapability, ParsedCommand, WindowReference, ApplicationReference,
    BrowserReference, ReferenceWrapper
)
from capabilities.response import CapabilityResponse
from handlers.window_handler import (
    handle_focus_window, handle_maximize_window, handle_minimize_window, 
    handle_restore_window, handle_toggle_minimize, handle_move_window, handle_resize_window
)
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
        return ["open", "close", "focus", "maximize", "minimize", "restore", "list", "toggle_minimize", "move", "resize"]

    @property
    def supported_objects(self) -> List[str]:
        return ["application", "window", "app", "notepad", "calculator", "chrome", "telegram"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        if parsed.verb in self.supported_verbs:
            if isinstance(parsed.target, BrowserReference) and parsed.verb == "open":
                return 0.0
            obj_lower = (parsed.object or "").lower()
            if parsed.verb == "open" and ("." in obj_lower or "http" in obj_lower):
                return 0.0
            if parsed.verb == "list" and "window" not in obj_lower and "app" not in obj_lower:
                return 0.0
            return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        target_name = None
        if isinstance(parsed.target, WindowReference):
            target_name = parsed.target.window_name
        elif isinstance(parsed.target, ApplicationReference):
            target_name = parsed.target.app_name
        elif isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value
        
        entities = dict(parsed.entities)
        if target_name:
            target_name_clean = target_name.lower()
            entities["app_name"] = target_name_clean
            entities["window_name"] = target_name_clean
        else:
            if "app_name" not in entities:
                entities["app_name"] = None
            if "window_name" not in entities:
                entities["window_name"] = None

        interpretation = f"Window action: '{parsed.verb}' on application/window '{target_name or parsed.object}'"
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
        elif parsed.verb == "toggle_minimize":
            res = handle_toggle_minimize(entities, context)
            verification_result = (res.get("status") == "success")
            if verification_result:
                payload = res.get("payload") or {}
                context_updates = {
                    "last_window_operation": "toggle_minimize",
                    "current_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window": payload.get("window_title") or entities.get("window_name"),
                    "last_window_handle": payload.get("window_handle")
                }
        elif parsed.verb == "move":
            res = handle_move_window(entities, context)
            verification_result = (res.get("status") == "success")
        elif parsed.verb == "resize":
            res = handle_resize_window(entities, context)
            verification_result = (res.get("status") == "success")
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
