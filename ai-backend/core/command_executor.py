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

        # Parse intent using existing intent_parser
        result = parse_intent(command)
        intent = result["intent"]
        entities = result["entities"]

        # Run context resolver if manager is present to perform pronoun/repeat resolution
        if context_manager:
            from core.context_resolver import ContextResolver
            resolver = ContextResolver()
            snapshot = context_manager.get_snapshot()
            resolved_command, resolved_intent, resolved_entities, direct_response = resolver.resolve(
                command, intent, entities, snapshot
            )
            
            if direct_response:
                return direct_response

            command = resolved_command
            intent = resolved_intent
            entities = resolved_entities

        # Inject raw command and context manager into context dict for downstream handlers
        if context is None:
            context = {}
        context["raw_command"] = command
        if context_manager:
            context["context_manager"] = context_manager

        # Route to appropriate handler using simple dict lookup
        handler = HANDLERS.get(intent, handle_general_chat)

        # Call handler and get response
        response = handler(entities, context)

        # Ensure response includes intent for debugging
        response["intent"] = intent

        if context_manager:
            execution_time = time.time() - t0
            if response.get("status") == "error":
                context_manager.update_from_failure(
                    command, response, execution_time, parent_command=parent_command
                )
            else:
                context_manager.update_from_execution(
                    command, response, execution_time, parent_command=parent_command
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
