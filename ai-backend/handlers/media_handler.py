"""
Media handlers - handles play_music and media_control intents.
"""

from typing import Dict, Optional

from managers.media_manager import play_media


def handle_media_control(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for media_control intent - supports play/pause/resume/next/previous actions."""
    action = entities.get("media_action")
    query = entities.get("media_query")

    if not action:
        return {
            "status": "error",
            "reply": "I couldn't determine the media action. Please specify play, pause, resume, next, or previous.",
            "payload": {}
        }

    try:
        action_lower = action.lower()

        if action_lower == "play":
            if query:
                success = play_media(query)

                if success:
                    return {
                        "status": "success",
                        "reply": f"Playing {query}",
                        "payload": {"action": "play", "query": query}
                    }
                else:
                    return {
                        "status": "error",
                        "reply": f"Failed to play {query}",
                        "payload": {"action": "play", "query": query}
                    }
            else:
                return {
                    "status": "error",
                    "reply": "Please specify what you want to play",
                    "payload": {"action": "play"}
                }

        elif action_lower == "pause":
            return {
                "status": "success",
                "reply": "Media paused",
                "payload": {"action": "pause"}
            }

        elif action_lower == "resume":
            return {
                "status": "success",
                "reply": "Media resumed",
                "payload": {"action": "resume"}
            }

        elif action_lower == "next":
            return {
                "status": "success",
                "reply": "Playing next track",
                "payload": {"action": "next"}
            }

        elif action_lower == "previous":
            return {
                "status": "success",
                "reply": "Playing previous track",
                "payload": {"action": "previous"}
            }

        else:
            return {
                "status": "error",
                "reply": f"Unknown media action: {action}",
                "payload": {"action": action}
            }

    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to control media: {str(e)}",
            "payload": {"error": str(e), "action": action}
        }


def handle_play_music(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """
    Handler for play_music - alias for media_control with play action.
    This function exists for backwards compatibility and clear separation.
    """
    entities["media_action"] = "play"
    return handle_media_control(entities, context)
