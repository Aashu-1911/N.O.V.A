"""
System handlers - handles lock_pc, take_screenshot, and volume_control intents.

All functions accept an ``entities`` dict (extracted by the intent parser) and an
optional ``context`` dict.  They return a ``ResponseDict`` built with
:mod:`core.response_builder` helpers.

This module has NO voice imports and NO HTTP framework imports.
"""

from typing import Any, Dict, Optional

from core.response_builder import success, error
from managers.system_manager import (
    lock_pc,
    take_screenshot,
    mute_volume,
    unmute_volume,
    volume_up,
    volume_down,
)

# Convenience alias for the structured response dict returned by every handler.
ResponseDict = Dict[str, Any]


def handle_lock_pc(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``lock_pc`` intent — lock the workstation screen.

    Args:
        entities: Intent entities (not used by this handler).
        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` on success, or ``status="error"``
        if the OS lock call raises an exception.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_lock_pc({})
        # {"status": "success", "reply": "Locking PC"}
    """
    try:
        lock_pc()
        return success("Locking PC")
    except Exception as e:
        return error(f"Failed to lock PC: {str(e)}", payload={"error": str(e)})


def handle_screenshot(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``take_screenshot`` intent — capture and save a screenshot.

    Args:
        entities: Intent entities (not used by this handler).
        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and the saved file path in
        ``payload["filepath"]``, or ``status="error"`` on failure.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_screenshot({})
        # {"status": "success", "reply": "Screenshot taken", "payload": {"filepath": "/path/to/screenshot.png"}}
    """
    try:
        filepath = take_screenshot()
        return success("Screenshot taken", payload={"filepath": filepath})
    except Exception as e:
        return error(f"Failed to take screenshot: {str(e)}", payload={"error": str(e)})


def handle_volume_control(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``volume_control`` intent — adjust system audio volume.

    Supported ``volume_action`` values (case-insensitive):

    - ``"mute"`` — mute the system volume.
    - ``"unmute"`` — unmute the system volume.
    - ``"up"`` / ``"increase"`` / ``"raise"`` — increase volume by one step.
    - ``"down"`` / ``"decrease"`` / ``"lower"`` — decrease volume by one step.

    Args:
        entities: Intent entities.  Expected keys:

            - ``volume_action`` *(str, required)* — the volume action to perform
              (see supported values above).

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and the action in ``payload["action"]``
        on success, or ``status="error"`` if the action is missing, unrecognised,
        or the OS call raises an exception.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_volume_control({"volume_action": "mute"})
        # {"status": "success", "reply": "Volume muted", "payload": {"action": "mute"}}

        result = handle_volume_control({"volume_action": "up"})
        # {"status": "success", "reply": "Volume increased", "payload": {"action": "up"}}
    """
    action = entities.get("volume_action")

    if not action:
        return error(
            "I couldn't determine the volume action. "
            "Please specify mute, unmute, volume up, or volume down."
        )

    try:
        action_lower = action.lower()

        if action_lower == "mute":
            mute_volume()
            reply = "Volume muted"
        elif action_lower == "unmute":
            unmute_volume()
            reply = "Volume unmuted"
        elif action_lower in ["up", "increase", "raise"]:
            volume_up()
            reply = "Volume increased"
        elif action_lower in ["down", "decrease", "lower"]:
            volume_down()
            reply = "Volume decreased"
        else:
            return error(f"Unknown volume action: {action}", payload={"action": action})

        return success(reply, payload={"action": action})

    except Exception as e:
        return error(
            f"Failed to control volume: {str(e)}",
            payload={"error": str(e), "action": action},
        )
