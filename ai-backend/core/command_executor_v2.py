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
from managers.browser_manager import open_website
from managers.app_manager import open_application, close_application


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
    """Handler for open_website intent - opens browser, websites, or performs web searches."""
    url = entities.get("url")
    
    # If no URL provided, open default browser
    if not url:
        try:
            success = open_website("https://www.google.com")
            if success:
                return {
                    "status": "success",
                    "reply": "Opening browser",
                    "payload": {"url": "https://www.google.com"}
                }
            else:
                return {
                    "status": "error",
                    "reply": "Failed to open browser",
                    "payload": {}
                }
        except Exception as e:
            return {
                "status": "error",
                "reply": f"Failed to open browser: {str(e)}",
                "payload": {"error": str(e)}
            }
    
    # Handle website/URL opening
    try:
        # Format URL properly
        formatted_url = url
        if not url.startswith(("http://", "https://")):
            # Check if it's a known website name
            if "." not in url:
                # Treat as search query or known site name
                formatted_url = f"https://www.{url}.com"
            else:
                formatted_url = f"https://{url}"
        
        success = open_website(formatted_url)
        
        if success:
            display_url = formatted_url.replace("https://", "").replace("http://", "")
            return {
                "status": "success",
                "reply": f"Opening {display_url}",
                "payload": {"url": formatted_url}
            }
        else:
            return {
                "status": "error",
                "reply": f"Could not open {url}",
                "payload": {"url": url}
            }
            
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to open website: {str(e)}",
            "payload": {"error": str(e), "url": url}
        }


def handle_search_web(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for search_web intent - performs web searches using Google."""
    search_query = entities.get("search_query")
    
    if not search_query:
        return {
            "status": "error",
            "reply": "I couldn't determine what to search for",
            "payload": {}
        }
    
    try:
        # Build Google search URL
        from urllib.parse import quote_plus
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
        
        success = open_website(search_url)
        
        if success:
            return {
                "status": "success",
                "reply": f"Searching for {search_query}",
                "payload": {"query": search_query, "url": search_url}
            }
        else:
            return {
                "status": "error",
                "reply": f"Failed to search for {search_query}",
                "payload": {"query": search_query}
            }
            
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to perform search: {str(e)}",
            "payload": {"error": str(e), "query": search_query}
        }


def handle_open_application(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for open_application intent."""
    app_name = entities.get("app_name")
    
    if not app_name:
        return {
            "status": "error",
            "reply": "I couldn't determine which application to open. Please specify the application name.",
            "payload": {}
        }
    
    try:
        success = open_application(app_name)
        
        if success:
            return {
                "status": "success",
                "reply": f"Opening {app_name}",
                "payload": {"app_name": app_name}
            }
        else:
            return {
                "status": "error",
                "reply": f"Could not find or open {app_name}",
                "payload": {"app_name": app_name}
            }
            
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to open application: {str(e)}",
            "payload": {"error": str(e), "app_name": app_name}
        }


def handle_close_application(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for close_application intent."""
    app_name = entities.get("app_name")
    
    if not app_name:
        return {
            "status": "error",
            "reply": "I couldn't determine which application to close. Please specify the application name.",
            "payload": {}
        }
    
    try:
        success = close_application(app_name)
        
        if success:
            return {
                "status": "success",
                "reply": f"Closed {app_name}",
                "payload": {"app_name": app_name}
            }
        else:
            return {
                "status": "error",
                "reply": f"Could not find or close {app_name}",
                "payload": {"app_name": app_name}
            }
            
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to close application: {str(e)}",
            "payload": {"error": str(e), "app_name": app_name}
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
    "search_web": handle_search_web,
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
