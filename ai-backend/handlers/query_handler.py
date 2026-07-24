from typing import Any, Dict, Optional
from core.response_builder import success, error

ResponseDict = Dict[str, Any]

def handle_query_context(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the query_context intent by accessing the ExecutionContextManager snapshot."""
    context_manager = context.get("context_manager") if context else None
    if not context_manager:
        return error("No context manager is currently active to answer that question.")

    query_type = entities.get("query_type")
    snapshot = context_manager.get_snapshot()

    if query_type == "current_website":
        if snapshot.current_url:
            display_url = snapshot.current_url.replace("https://", "").replace("http://", "").replace("www.", "")
            return success(f"You are currently on {display_url}.", payload={"url": snapshot.current_url})
        else:
            return success("I don't think you are on any website right now.", payload={"url": None})

    elif query_type == "current_application":
        if snapshot.current_application:
            return success(f"You currently have {snapshot.current_application} open.", payload={"app_name": snapshot.current_application})
        else:
            return success("No application is currently recorded as open.", payload={"app_name": None})

    elif query_type == "last_opened_application":
        if snapshot.last_opened_application:
            return success(f"I just opened {snapshot.last_opened_application}.", payload={"app_name": snapshot.last_opened_application})
        else:
            return success("I haven't opened any application recently.", payload={"app_name": None})

    return error("I'm sorry, I couldn't resolve that context query.")


def handle_browser_back(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle browser navigation back simulation."""
    context_manager = context.get("context_manager") if context else None
    if context_manager:
        snapshot = context_manager.get_snapshot()
        if snapshot.current_browser:
            return success(f"Navigating back in {snapshot.current_browser}.", payload={"action": "go_back"})
    return success("Going back.", payload={"action": "go_back"})
