from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand, ReferenceWrapper
from capabilities.response import CapabilityResponse
from handlers.chat_handler import handle_general_chat

class GeneralLLMCapability(BaseCapability):
    """Fallback LLM-based subsystem capability for general question answering and text generation."""

    @property
    def name(self) -> str:
        return "GeneralLLMCapability"

    def priority(self) -> int:
        return 10

    @property
    def supported_verbs(self) -> List[str]:
        return ["explain", "write", "translate", "summarize", "chat", "ask"]

    @property
    def supported_objects(self) -> List[str]:
        return []

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        # STRICT CONSTRAINT: Never answer screen, UI, or automation requests.
        # These must be handled by Vision, OCR, or UIAutomation placeholders.
        ui_screen_keywords = {
            "screen", "button", "textbox", "checkbox", "controls", "label",
            "popup", "window", "click", "type", "select", "locate", "describe", "read"
        }
        words = set(parsed.raw_command.lower().split())
        
        # Exception: "read text" from image goes to OCR, "read popup" goes to Vision.
        # But general conversation might have "read" or "describe". If combined with UI elements or screen, exclude.
        if words.intersection(ui_screen_keywords):
            if "screen" in words or "button" in words or "textbox" in words or "popup" in words or "controls" in words:
                return 0.0
            if "click" in words or "locate" in words:
                return 0.0

        # LLM capability is open-ended and serves as the catch-all fallback
        return 0.1

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        entities = dict(parsed.entities)
        interpretation = f"General LLM fallback query: '{parsed.raw_command}'"
        res = handle_general_chat(entities, context)
        verification_result = (res.get("status") == "success")

        return CapabilityResponse(
            status=res.get("status", "success"),
            reply=res.get("reply", ""),
            payload={
                "interpretation": interpretation,
                "execution_summary": "LLM response generation completed",
                **res.get("payload", {})
            },
            verification_result=verification_result
        )

class ClipboardCapability(BaseCapability):
    """Subsystem capability representing OS clipboard functions."""

    @property
    def name(self) -> str:
        return "ClipboardCapability"

    def priority(self) -> int:
        return 85

    @property
    def supported_verbs(self) -> List[str]:
        return ["copy", "paste", "clipboard_copy", "clipboard_paste"]

    @property
    def supported_objects(self) -> List[str]:
        return ["clipboard", "text"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if "clipboard" in obj_lower or "text" in obj_lower:
                return 1.0
            if parsed.verb in {"clipboard_copy", "clipboard_paste"}:
                return 1.0
        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        import pyperclip
        target_name = parsed.object
        if isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value

        interpretation = f"Clipboard action: '{parsed.verb}'"
        context_updates = {}
        
        if parsed.verb in {"copy", "clipboard_copy"}:
            text_to_copy = parsed.entities.get("text", target_name)
            pyperclip.copy(text_to_copy)
            reply = "Copied to clipboard."
            context_updates = {"clipboard": text_to_copy}
            verification_result = True
        elif parsed.verb in {"paste", "clipboard_paste"}:
            reply = pyperclip.paste()
            context_updates = {}
            verification_result = True
        else:
            reply = "Unsupported clipboard action."
            verification_result = False

        return CapabilityResponse(
            status="success" if verification_result else "error",
            reply=reply,
            payload={
                "interpretation": interpretation,
                "execution_summary": reply
            },
            verification_result=verification_result,
            context_updates=context_updates
        )

class SystemCapability(BaseCapability):
    """Subsystem capability representing general system control like screenshooting or locking."""

    @property
    def name(self) -> str:
        return "SystemCapability"

    def priority(self) -> int:
        return 85

    @property
    def supported_verbs(self) -> List[str]:
        return ["lock", "screenshot", "reminder"]

    @property
    def supported_objects(self) -> List[str]:
        return ["pc", "computer", "screen", "screenshot", "reminder"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        if parsed.verb in self.supported_verbs:
            return 1.0
        if "lock" in parsed.raw_command.lower() and "pc" in parsed.raw_command.lower():
            return 1.0
        if "screenshot" in parsed.raw_command.lower():
            return 1.0
        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        from handlers.system_handler import handle_lock_pc, handle_screenshot
        entities = dict(parsed.entities)
        interpretation = f"System action: '{parsed.verb}'"
        verification_result = False

        if parsed.verb == "lock" or "lock" in parsed.raw_command.lower():
            res = handle_lock_pc(entities, context)
            verification_result = (res.get("status") == "success")
        elif parsed.verb == "screenshot" or "screenshot" in parsed.raw_command.lower():
            res = handle_screenshot(entities, context)
            verification_result = (res.get("status") == "success")
        elif parsed.verb == "reminder":
            res = {
                "status": "success",
                "reply": "Handler not implemented yet - reminder",
                "payload": {}
            }
            verification_result = True
        else:
            res = {"status": "error", "reply": "Unsupported system action."}

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

class TaskManagementCapability(BaseCapability):
    """Subsystem capability representing N.O.V.A.'s tasks database operations."""

    @property
    def name(self) -> str:
        return "TaskManagementCapability"

    def priority(self) -> int:
        return 85

    @property
    def supported_verbs(self) -> List[str]:
        return ["add", "complete", "show", "update", "list"]

    @property
    def supported_objects(self) -> List[str]:
        return ["task", "tasks", "stats"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0
        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        from handlers.task_handler import (
            handle_add_task, handle_show_tasks, handle_complete_task,
            handle_show_stats, handle_update_task
        )
        target_name = parsed.object
        if isinstance(parsed.target, ReferenceWrapper):
            target_name = parsed.target.value

        entities = dict(parsed.entities)
        # Handle entities mapping if missing
        if not entities.get("title") and parsed.verb == "add" and target_name:
            entities["title"] = target_name.replace("task", "").strip()
        if not entities.get("task_id") and parsed.verb == "complete" and target_name:
            try:
                entities["task_id"] = int(target_name.replace("task", "").strip())
            except ValueError:
                pass

        interpretation = f"Task action: '{parsed.verb}' with target '{target_name or parsed.object}'"

        if parsed.verb == "add":
            res = handle_add_task(entities, context)
            verification_result = (res.get("status") == "success")
        elif parsed.verb in {"show", "list"}:
            if target_name and "stat" in target_name.lower():
                res = handle_show_stats(entities, context)
            else:
                res = handle_show_tasks(entities, context)
            verification_result = (res.get("status") == "success")
        elif parsed.verb == "complete":
            res = handle_complete_task(entities, context)
            verification_result = (res.get("status") == "success")
        elif parsed.verb == "update":
            res = handle_update_task(entities, context)
            verification_result = (res.get("status") == "success")
        else:
            res = {"status": "error", "reply": "Unsupported task action."}
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
