"""
System handlers - handles lock_pc, take_screenshot, and volume_control intents.
"""

from typing import Dict, Optional

from managers.system_manager import (
    lock_pc,
    take_screenshot,
    mute_volume,
    unmute_volume,
    volume_up,
    volume_down,
)


def handle_lock_pc(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for lock_pc intent."""
    try:
        lock_pc()
        return {
            "status": "success",
            "reply": "Locking PC",
            "payload": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to lock PC: {str(e)}",
            "payload": {"error": str(e)}
        }


def handle_screenshot(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for take_screenshot intent."""
    try:
        filepath = take_screenshot()
        return {
            "status": "success",
            "reply": "Screenshot taken",
            "payload": {"filepath": filepath}
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to take screenshot: {str(e)}",
            "payload": {"error": str(e)}
        }


def handle_volume_control(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for volume_control intent - supports mute/unmute/up/down actions."""
    action = entities.get("volume_action")

    if not action:
        return {
            "status": "error",
            "reply": "I couldn't determine the volume action. Please specify mute, unmute, volume up, or volume down.",
            "payload": {}
        }

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
            return {
                "status": "error",
                "reply": f"Unknown volume action: {action}",
                "payload": {"action": action}
            }

        return {
            "status": "success",
            "reply": reply,
            "payload": {"action": action}
        }

    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to control volume: {str(e)}",
            "payload": {"error": str(e), "action": action}
        }
