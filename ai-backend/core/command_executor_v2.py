"""
Command Executor V2 - Skeleton routing layer with simple HANDLERS dict.

This is a minimal routing layer that:
1. Parses intent using intent_parser
2. Routes to appropriate handler using simple HANDLERS dict
3. Returns manual dict format: {"status": "success", "reply": "...", "payload": {...}}

DO NOT import manager modules yet - handlers are stubs.
DO NOT create response_builder yet - using manual dicts.
"""

from typing import Dict, Optional
from core.intent_parser import parse_intent
from managers.task_manager import add_task, complete_task, get_tasks, get_task_stats


# ============================================================================
# Handler Stub Functions
# ============================================================================

def handle_add_task(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for add_task intent."""
    task_name = entities.get("task_name")
    
    if not task_name:
        return {
            "status": "error",
            "reply": "I couldn't determine the task name. Please try again.",
            "payload": {}
        }
    
    try:
        task = add_task(
            task_name=task_name,
            date=entities.get("date"),
            category=entities.get("category"),
            priority=entities.get("priority")
        )
        return {
            "status": "success",
            "reply": f"Added task: {task_name}",
            "payload": task
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to add task: {str(e)}",
            "payload": {"error": str(e)}
        }


def handle_show_tasks(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for show_tasks intent."""
    try:
        # Check if user wants only pending tasks
        include_completed = entities.get("include_completed", False)
        tasks = get_tasks(include_completed=include_completed)
        
        if not tasks:
            return {
                "status": "success",
                "reply": "You have no tasks.",
                "payload": {"tasks": []}
            }
        
        # Format task list for display
        task_list = []
        for task in tasks:
            status = "✓" if task["completed"] else "○"
            task_str = f"{status} {task['task_name']}"
            if task.get("date"):
                task_str += f" (due: {task['date']})"
            task_list.append(task_str)
        
        reply = f"Here are your tasks:\n" + "\n".join(task_list)
        return {
            "status": "success",
            "reply": reply,
            "payload": {"tasks": tasks}
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": "Failed to fetch tasks.",
            "payload": {"error": str(e)}
        }


def handle_complete_task(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for complete_task intent."""
    task_identifier = entities.get("task_name") or entities.get("task_id")
    
    if not task_identifier:
        return {
            "status": "error",
            "reply": "I couldn't determine which task to complete. Please specify the task name or ID.",
            "payload": {}
        }
    
    try:
        task = complete_task(task_identifier)
        
        if not task:
            return {
                "status": "error",
                "reply": f"Task '{task_identifier}' not found.",
                "payload": {}
            }
        
        return {
            "status": "success",
            "reply": f"Completed task: {task['task_name']}",
            "payload": task
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to complete task: {str(e)}",
            "payload": {"error": str(e)}
        }


def handle_show_stats(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for show_stats intent."""
    try:
        stats = get_task_stats()
        reply = f"You have {stats['pending']} pending and {stats['completed']} completed tasks."
        
        return {
            "status": "success",
            "reply": reply,
            "payload": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": "Failed to get task statistics.",
            "payload": {"error": str(e)}
        }


def handle_update_task(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for update_task intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - update_task",
        "payload": {}
    }


def handle_open_website(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for open_website intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - open_website",
        "payload": {}
    }


def handle_open_application(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for open_application intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - open_application",
        "payload": {}
    }


def handle_close_application(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for close_application intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - close_application",
        "payload": {}
    }


def handle_lock_pc(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for lock_pc intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - lock_pc",
        "payload": {}
    }


def handle_screenshot(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for take_screenshot intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - take_screenshot",
        "payload": {}
    }


def handle_volume_control(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for volume_control intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - volume_control",
        "payload": {}
    }


def handle_media_control(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for media_control intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - media_control",
        "payload": {}
    }


def handle_reminder(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for reminder intent."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - reminder",
        "payload": {}
    }


def handle_general_chat(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for general chat and fallback."""
    return {
        "status": "success",
        "reply": "Handler not implemented yet - general_chat",
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
    "open_application": handle_open_application,
    "close_application": handle_close_application,
    "lock_pc": handle_lock_pc,
    "take_screenshot": handle_screenshot,
    "volume_control": handle_volume_control,
    "media_control": handle_media_control,
    "reminder": handle_reminder,
    "answer_question": handle_general_chat,  # Default intent from intent_parser
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
