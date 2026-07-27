"""
Command Executor — thin routing layer that dispatches intents to handler functions.

Architecture position
---------------------
This module sits at the centre of the three-layer architecture::

    INPUT ADAPTERS          CORE LAYER              OUTPUT / ADAPTERS
    ──────────────          ──────────              ─────────────────
    adapters/voice_adapter  →  command_executor  →  (response dict returned)
    api/routes.py           →        ↑
                               handlers/*
                               core/response_builder

Responsibilities
----------------
1. Parse the raw command string into an intent + entities via ``intent_parser``.
2. Look up the appropriate handler in the ``HANDLERS`` dict.
3. Call the handler and return its standardised response dict.
4. Inject the intent name into the response for debugging.
5. Catch unexpected exceptions and return a safe error response.

**This module has NO voice imports and NO HTTP framework imports.**
It is intentionally interface-agnostic: it does not call ``speak()``, does not
import FastAPI, and does not know whether the caller is a voice adapter, an HTTP
route, a GUI, or a CLI.

Handler implementations live in ``handlers/``.
Response helpers live in ``core/response_builder``.
"""

import time
from typing import Any, Dict, Optional

from core.command_chain import split_commands, execute_chain
from core.intent_parser import parse_intent
from handlers.task_handler import (
    handle_add_task,
    handle_show_tasks,
    handle_complete_task,
    handle_show_stats,
    handle_update_task,
)
from handlers.browser_handler import handle_open_website, handle_search_web
from handlers.app_handler import handle_open_application, handle_close_application
from handlers.system_handler import handle_lock_pc, handle_screenshot, handle_volume_control
from handlers.media_handler import handle_play_music, handle_media_control
from handlers.chat_handler import handle_general_chat
from handlers.window_handler import (
    handle_focus_window,
    handle_maximize_window,
    handle_minimize_window,
    handle_restore_window,
    handle_list_windows,
    handle_get_active_window,
)
from handlers.query_handler import handle_query_context, handle_browser_back

# Convenience alias used in this module and re-usable by callers.
ResponseDict = Dict[str, Any]


def handle_reminder(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Stub handler for the ``reminder`` intent (not yet implemented).

    Args:
        entities: Intent entities (ignored by stub).
        context: Optional session / request context (ignored by stub).

    Returns:
        ResponseDict with ``status="success"`` and a placeholder reply.
    """
    return {
        "status": "success",
        "reply": "Handler not implemented yet - reminder",
        "payload": {},
    }


# ============================================================================
# Simple HANDLERS Dict — maps intent name → handler callable
# ============================================================================

HANDLERS: Dict[str, Any] = {
    "add_task": handle_add_task,
    "show_tasks": handle_show_tasks,
    "complete_task": handle_complete_task,
    "show_stats": handle_show_stats,
    "update_task": handle_update_task,
    "open_website": handle_open_website,
    "search_web": handle_search_web,
    "open_application": handle_open_application,
    "close_application": handle_close_application,
    "lock_pc": handle_lock_pc,
    "take_screenshot": handle_screenshot,
    "volume_control": handle_volume_control,
    "media_control": handle_media_control,
    "play_music": handle_play_music,
    "reminder": handle_reminder,
    "focus_window": handle_focus_window,
    "maximize_window": handle_maximize_window,
    "minimize_window": handle_minimize_window,
    "restore_window": handle_restore_window,
    "list_windows": handle_list_windows,
    "get_active_window": handle_get_active_window,
    "answer_question": handle_general_chat,  # Default intent from intent_parser
    "general_chat": handle_general_chat,      # Alias for explicit general_chat intent
    "query_context": handle_query_context,
    "browser_go_back": handle_browser_back,
}


# ============================================================================
# Private single-command execution path
# ============================================================================

def get_legacy_intent_name(capability_name: str, verb: str, obj: str = "") -> str:
    """Map capability and parsed verb to legacy intent name for backward compatibility."""
    verb_lower = (verb or "").lower()
    obj_lower = (obj or "").lower()
    
    if capability_name == "WindowCapability":
        if verb_lower == "open":
            return "open_application"
        if verb_lower == "close":
            return "close_application"
        if verb_lower == "focus":
            return "focus_window"
        if verb_lower == "maximize":
            return "maximize_window"
        if verb_lower == "minimize":
            return "minimize_window"
        if verb_lower == "restore":
            return "restore_window"
        if verb_lower == "list":
            return "list_windows"
            
    elif capability_name == "BrowserCapability":
        if verb_lower == "open":
            return "open_website"
        if verb_lower == "search":
            return "search_web"
        if verb_lower == "go":
            return "browser_go_back"
        if verb_lower == "refresh":
            return "browser_refresh"
            
    elif capability_name == "VolumeCapability":
        return "volume_control"
        
    elif capability_name == "MediaCapability":
        return "media_control"
        
    elif capability_name == "TaskManagementCapability":
        if verb_lower == "add":
            return "add_task"
        if verb_lower == "complete":
            return "complete_task"
        if verb_lower == "update":
            return "update_task"
        if verb_lower in {"show", "list"}:
            if "stat" in obj_lower:
                return "show_stats"
            return "show_tasks"
            
    elif capability_name == "SystemCapability":
        if verb_lower == "lock" or "lock" in verb_lower:
            return "lock_pc"
        if verb_lower == "screenshot":
            return "take_screenshot"
        if verb_lower == "reminder":
            return "reminder"
            
    elif capability_name == "ConversationCapability":
        return "query_context"
        
    elif capability_name == "GeneralLLMCapability":
        return "general_chat"
        
    return verb_lower or "unknown"


def execute_single(
    command: str,
    context: Optional[Dict[str, Any]] = None,
    context_manager: Optional[Any] = None,
    parent_command: Optional[str] = None,
) -> ResponseDict:
    """Internal single-command execution path: intent parse → handler → response.

    This function runs one command through the full pipeline without any
    chain detection.  It must **not** call ``split_commands()`` or
    ``execute_chain()`` — doing so would allow re-entrant chain execution.

    Args:
        command: A single raw command string.
        context: Optional context dict (``raw_command`` is auto-populated).
        context_manager: Optional ExecutionContextManager instance.
        parent_command: Optional top-level user command if this is a sub-command.

    Returns:
        ResponseDict from the matched handler, with ``intent`` injected.
    """
    t0 = time.time()
    try:
        # Normalize action verbs to canonical form before intent parsing
        from core.context_resolver import normalize_command_verbs
        command = normalize_command_verbs(command)

        # 1. Parse the command using lightweight CommandParser
        from capabilities import CommandParser
        parsed_cmd = CommandParser.parse(command)

        # 2. Context Resolver performs pronoun and repeat resolution before routing
        from core.context_resolver import ContextResolver
        from core.execution_context import ExecutionContext
        resolver = ContextResolver()
        if context_manager:
            snapshot = context_manager.get_snapshot()
        else:
            snapshot = ExecutionContext()
            if context:
                for k, v in context.items():
                    if hasattr(snapshot, k):
                        setattr(snapshot, k, v)
        
        resolved_cmd = resolver.resolve(parsed_cmd, snapshot)

        # If resolver generated a NeedsClarification target
        from capabilities.base import NeedsClarification
        if isinstance(resolved_cmd.target, NeedsClarification):
            status = "success" if resolved_cmd.verb in {"open", "close"} else "error"
            response = {
                "status": status,
                "reply": resolved_cmd.target.reply,
                "intent": get_legacy_intent_name("CapabilityRouter", resolved_cmd.verb, resolved_cmd.object),
                "payload": {"error": "missing_context"}
            }
            if context_manager:
                execution_time = time.time() - t0
                if status == "error":
                    context_manager.update_from_failure(
                        resolved_cmd.raw_command, response, execution_time, parent_command=parent_command
                    )
                else:
                    context_manager.update_from_execution(
                        resolved_cmd.raw_command, response, execution_time, parent_command=parent_command
                    )
            return response

        # If resolver generated a direct clarification response
        if resolved_cmd.direct_response is not None:
            response = resolved_cmd.direct_response
            if context_manager:
                execution_time = time.time() - t0
                context_manager.update_from_execution(
                    resolved_cmd.raw_command, response, execution_time, parent_command=parent_command
                )
            return response

        # 3. Inject context manager and resolved raw command
        if context is None:
            context = {}
        context["raw_command"] = resolved_cmd.raw_command
        if context_manager:
            context["context_manager"] = context_manager

        # 4. Route and dispatch via central CapabilityRouter
        from capabilities import CapabilityRouter
        router = CapabilityRouter()
        cap_response = router.route_and_dispatch(resolved_cmd, context)

        # Convert to dictionary layout preserving backward compatibility
        response = cap_response.to_dict()
        legacy_intent = get_legacy_intent_name(cap_response.handled_by, resolved_cmd.verb, resolved_cmd.object)
        response["intent"] = legacy_intent

        if context_manager:
            execution_time = time.time() - t0
            if response.get("status") == "error":
                context_manager.update_from_failure(
                    resolved_cmd.raw_command, response, execution_time, parent_command=parent_command
                )
            else:
                context_manager.update_from_execution(
                    resolved_cmd.raw_command,
                    response,
                    execution_time,
                    parent_command=parent_command,
                    context_updates=cap_response.context_updates,
                    entities=resolved_cmd.entities
                )

        return response

    except Exception as e:
        # Error handling — return safe fallback dict
        response = {
            "status": "error",
            "reply": "I'm sorry, something went wrong processing that command.",
            "payload": {"error": str(e)},
            "intent": "unknown",
        }
        if context_manager:
            execution_time = time.time() - t0
            context_manager.update_from_failure(
                command, response, execution_time, parent_command=parent_command
            )
        return response


# ============================================================================
# Public API
# ============================================================================

def execute_command(
    command: str,
    context: Optional[Dict[str, Any]] = None,
    context_manager: Optional[Any] = None,
) -> ResponseDict:
    """Execute a natural-language command and return a structured response dict.

    This is the **single entry point** for all commands regardless of origin
    (voice, HTTP, GUI, CLI, etc.).  The caller is responsible for any
    interface-specific output (calling ``speak()``, serialising to JSON, etc.).

    Args:
        command: Raw command text (e.g. ``"Add task to learn Docker"``).
        context: Optional context dict.  Common keys:
            - ``raw_command`` — auto-populated by this function.
            - ``user_id`` — optional user identifier for multi-user scenarios.
            - ``session_id`` — optional session identifier.
        context_manager: Optional ExecutionContextManager instance.

    Returns:
        ResponseDict with standard keys: status, reply, intent, payload, metadata.
    """
    commands = split_commands(command)
    if len(commands) >= 2:
        return execute_chain(
            commands,
            lambda cmd, ctx: execute_single(cmd, ctx, context_manager, parent_command=command)
        )
    return execute_single(command, context, context_manager)
