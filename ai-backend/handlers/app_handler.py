"""
App handlers - handles open_application and close_application intents.

All functions accept an ``entities`` dict (extracted by the intent parser) and an
optional ``context`` dict.  They return a ``ResponseDict`` built with
:mod:`core.response_builder` helpers.

This module has NO voice imports and NO HTTP framework imports.
"""

from typing import Any, Dict, Optional

from core.response_builder import success, error
from managers.app_manager import open_application, close_application

# Convenience alias for the structured response dict returned by every handler.
ResponseDict = Dict[str, Any]


def handle_open_application(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``open_application`` intent — launch a desktop application.

    Args:
        entities: Intent entities.  Expected keys:

            - ``app_name`` *(str, required)* — name of the application to open
              (e.g. ``"Telegram"``, ``"Notepad"``, ``"Chrome"``).

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and ``payload["app_name"]`` on
        success, or ``status="error"`` if the application name is missing or the
        OS cannot find/launch the app.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_open_application({"app_name": "Notepad"})
        # {"status": "success", "reply": "Opening Notepad", "payload": {"app_name": "Notepad"}}
    """
    app_name = entities.get("app_name")

    if not app_name:
        return error(
            "I couldn't determine which application to open. "
            "Please specify the application name."
        )

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


def handle_close_application(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``close_application`` intent — terminate a running desktop application.

    Args:
        entities: Intent entities.  Expected keys:

            - ``app_name`` *(str, required)* — name of the application to close
              (e.g. ``"Telegram"``, ``"Notepad"``).

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and ``payload["app_name"]`` on
        success, or ``status="error"`` if the application name is missing or the
        process cannot be found/terminated.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_close_application({"app_name": "Telegram"})
        # {"status": "success", "reply": "Closed Telegram", "payload": {"app_name": "Telegram"}}
    """
    app_name = entities.get("app_name")

    if not app_name:
        return error(
            "I couldn't determine which application to close. "
            "Please specify the application name."
        )

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
