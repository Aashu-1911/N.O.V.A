"""
App handlers - handles open_application and close_application intents.
"""

from typing import Dict, Optional

from managers.app_manager import open_application, close_application


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
