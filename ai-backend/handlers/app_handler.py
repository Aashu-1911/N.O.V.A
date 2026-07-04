"""
App handlers - handles open_application and close_application intents.
"""

from typing import Dict, Optional

from core.response_builder import success, error
from managers.app_manager import open_application, close_application


def handle_open_application(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for open_application intent."""
    app_name = entities.get("app_name")

    if not app_name:
        return error("I couldn't determine which application to open. Please specify the application name.")

    try:
        result = open_application(app_name)

        if result:
            return success(f"Opening {app_name}", payload={"app_name": app_name})
        else:
            return error(f"Could not find or open {app_name}", payload={"app_name": app_name})

    except Exception as e:
        return error(
            f"Failed to open application: {str(e)}",
            payload={"error": str(e), "app_name": app_name},
        )


def handle_close_application(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for close_application intent."""
    app_name = entities.get("app_name")

    if not app_name:
        return error("I couldn't determine which application to close. Please specify the application name.")

    try:
        result = close_application(app_name)

        if result:
            return success(f"Closed {app_name}", payload={"app_name": app_name})
        else:
            return error(f"Could not find or close {app_name}", payload={"app_name": app_name})

    except Exception as e:
        return error(
            f"Failed to close application: {str(e)}",
            payload={"error": str(e), "app_name": app_name},
        )
