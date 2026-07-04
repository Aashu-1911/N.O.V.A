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
    "answer_question": handle_general_chat,  # Default intent from intent_parser
    "general_chat": handle_general_chat,      # Alias for explicit general_chat intent
}


# ============================================================================
# Private single-command execution path
# ============================================================================

def execute_single(
    command: str,
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Internal single-command execution path: intent parse → handler → response.

    This function runs one command through the full pipeline without any
    chain detection.  It must **not** call ``split_commands()`` or
    ``execute_chain()`` — doing so would allow re-entrant chain execution.

    Args:
        command: A single raw command string.
        context: Optional context dict (``raw_command`` is auto-populated).

    Returns:
        ResponseDict from the matched handler, with ``intent`` injected.
    """
    try:
        # Parse intent using existing intent_parser
        result = parse_intent(command)
        intent = result["intent"]
        entities = result["entities"]

        # Inject raw command into context so handlers (especially general_chat) can access it
        if context is None:
            context = {}
        context["raw_command"] = command

        # Route to appropriate handler using simple dict lookup
        handler = HANDLERS.get(intent, handle_general_chat)

        # Call handler and get response
        response = handler(entities, context)

        # Ensure response includes intent for debugging
        response["intent"] = intent

        return response

    except Exception as e:
        # Error handling — return safe fallback dict
        return {
            "status": "error",
            "reply": "I'm sorry, something went wrong processing that command.",
            "payload": {"error": str(e)},
            "intent": "unknown",
        }


# ============================================================================
# Public API
# ============================================================================

def execute_command(
    command: str,
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Execute a natural-language command and return a structured response dict.

    This is the **single entry point** for all commands regardless of origin
    (voice, HTTP, GUI, CLI, etc.).  The caller is responsible for any
    interface-specific output (calling ``speak()``, serialising to JSON, etc.).

    Steps performed:

    1. Parse ``command`` into an intent + entities via :mod:`core.intent_parser`.
    2. Inject ``command`` into ``context["raw_command"]`` so fallback handlers
       (e.g. :func:`handlers.chat_handler.handle_general_chat`) can access it.
    3. Look up the handler in :data:`HANDLERS`; fall back to
       :func:`handlers.chat_handler.handle_general_chat` for unknown intents.
    4. Call the handler and attach the ``intent`` key to the response.

    Args:
        command: Raw command text (e.g. ``"Add task to learn Docker"``).
        context: Optional context dict.  Common keys:

            - ``raw_command`` — auto-populated by this function.
            - ``user_id`` — optional user identifier for multi-user scenarios.
            - ``session_id`` — optional session identifier.

    Returns:
        ResponseDict with the following keys:

        - ``status`` *(str)* — ``"success"``, ``"error"``, or ``"partial"``.
        - ``reply`` *(str)* — human-readable response text for the user.
        - ``intent`` *(str)* — detected intent name (useful for debugging).
        - ``payload`` *(dict | None)* — optional additional structured data.
        - ``metadata`` *(dict | None)* — optional debug / diagnostic data.

    Example::

        response = execute_command("Add task to learn Docker")
        # {
        #   "status": "success",
        #   "reply": "Added task: learn Docker",
        #   "intent": "add_task",
        #   "payload": {"task_id": 42, ...},
        # }

        response = execute_command("How are you?")
        # {"status": "success", "reply": "I'm doing well! ...", "intent": "answer_question"}
    """
    commands = split_commands(command)
    if len(commands) >= 2:
        return execute_chain(commands, execute_single)
    return execute_single(command, context)
