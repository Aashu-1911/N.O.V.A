"""
Command Executor - Routing layer that dispatches intents to handler functions.

This module:
1. Parses intent using intent_parser
2. Routes to the appropriate handler via the HANDLERS dict
3. Returns standardized response dict: {"status": "...", "reply": "...", "payload": {...}}

Handler implementations live in handlers/*.
"""

from typing import Dict, Optional

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


def handle_reminder(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for reminder intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - reminder",
        "payload": {}
    }


# ============================================================================
# Simple HANDLERS Dict - Maps intent to handler function
# ============================================================================

HANDLERS = {
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
# Main Execute Command Function - Minimal routing layer
# ============================================================================

def execute_command(command: str, context: Optional[Dict] = None) -> Dict:
    """
    Execute a command by routing to appropriate handler.

    This is a THIN routing layer that:
    1. Parses intent using intent_parser
    2. Routes to handler using HANDLERS dict
    3. Returns standardized response dict

    Args:
        command: Command text (e.g., "Add task to learn Docker")
        context: Optional context dict (user_id, session_id, etc.)

    Returns:
        Response dict with keys:
        - status: "success" | "error" | "partial"
        - reply: User-facing response text
        - payload: Optional additional data
        - intent: Intent name for debugging
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
        # Error handling - return manual dict
        return {
            "status": "error",
            "reply": "I'm sorry, something went wrong processing that command.",
            "payload": {"error": str(e)},
            "intent": "unknown"
        }
