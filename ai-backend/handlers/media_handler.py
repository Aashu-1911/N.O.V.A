"""
Media handlers - handles play_music and media_control intents.

All functions accept an ``entities`` dict (extracted by the intent parser) and an
optional ``context`` dict.  They return a ``ResponseDict`` built with
:mod:`core.response_builder` helpers.

This module has NO voice imports and NO HTTP framework imports.
"""

from typing import Any, Dict, Optional

from core.response_builder import success, error
from managers.media_manager import play_media

# Convenience alias for the structured response dict returned by every handler.
ResponseDict = Dict[str, Any]


def handle_media_control(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``media_control`` intent — control media playback.

    Supported ``media_action`` values (case-insensitive):

    - ``"play"`` — start or resume playback; ``media_query`` is used when present.
    - ``"pause"`` — pause current playback.
    - ``"resume"`` — resume paused playback.
    - ``"next"`` — skip to the next track.
    - ``"previous"`` — go back to the previous track.

    Args:
        entities: Intent entities.  Expected keys:

            - ``media_action`` *(str, required)* — one of the actions listed above.
            - ``media_query`` *(str, optional)* — search query used when
              ``media_action`` is ``"play"`` (e.g. ``"classical music"``).

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and action details in ``payload``,
        or ``status="error"`` if the action is missing, unrecognised, or the
        media manager raises an exception.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_media_control({"media_action": "pause"})
        # {"status": "success", "reply": "Media paused", "payload": {"action": "pause"}}

        result = handle_media_control({"media_action": "play", "media_query": "jazz"})
        # {"status": "success", "reply": "Playing jazz", "payload": {"action": "play", "query": "jazz"}}
    """
    action = entities.get("media_action")
    query = entities.get("media_query")

    if not action:
        return error(
            "I couldn't determine the media action. "
            "Please specify play, pause, resume, next, or previous."
        )

    try:
        action_lower = action.lower()

        if action_lower == "play":
            if query:
                result = play_media(query)
                if result:
                    return success(f"Playing {query}", payload={"action": "play", "query": query})
                else:
                    return error(f"Failed to play {query}", payload={"action": "play", "query": query})
            else:
                return error("Please specify what you want to play", payload={"action": "play"})

        elif action_lower == "pause":
            return success("Media paused", payload={"action": "pause"})

        elif action_lower == "resume":
            return success("Media resumed", payload={"action": "resume"})

        elif action_lower == "next":
            return success("Playing next track", payload={"action": "next"})

        elif action_lower == "previous":
            return success("Playing previous track", payload={"action": "previous"})

        else:
            return error(f"Unknown media action: {action}", payload={"action": action})

    except Exception as e:
        return error(
            f"Failed to control media: {str(e)}",
            payload={"error": str(e), "action": action},
        )


def handle_play_music(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``play_music`` intent — convenience wrapper for media play action.

    Delegates to :func:`handle_media_control` after injecting
    ``media_action="play"`` into ``entities``.  Exists for backward
    compatibility and for explicit intent routing in the HANDLERS dict.

    Args:
        entities: Intent entities.  Expected keys:

            - ``media_query`` *(str, optional)* — what to play (e.g. ``"jazz"``).

        context: Optional session / request context (passed through to
            :func:`handle_media_control`).

    Returns:
        ResponseDict as returned by :func:`handle_media_control`.

    Example::

        result = handle_play_music({"media_query": "lo-fi beats"})
        # {"status": "success", "reply": "Playing lo-fi beats", "payload": {"action": "play", "query": "lo-fi beats"}}
    """
    entities["media_action"] = "play"
    return handle_media_control(entities, context)
