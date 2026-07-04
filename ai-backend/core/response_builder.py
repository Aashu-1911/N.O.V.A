"""
Response builder - standardized response construction helpers.

Provides success(), error(), and partial() factory functions that return
consistently structured response dicts for use across all handlers.
"""

from typing import Dict, Optional


def success(
    reply: str,
    payload: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> Dict:
    """
    Build a success response dict.

    Args:
        reply: User-facing response text.
        payload: Optional data payload (e.g., task object, stats dict).
        metadata: Optional metadata (e.g., debug info, entities, confidence).

    Returns:
        Dict with keys: ``status`` (``"success"``), ``reply``, and optionally
        ``payload`` and ``metadata`` when they are not None.

    Example::

        return success("Added task: learn Docker", payload={"task_id": 42})
    """
    response: Dict = {"status": "success", "reply": reply}
    if payload is not None:
        response["payload"] = payload
    if metadata is not None:
        response["metadata"] = metadata
    return response


def error(
    reply: str,
    payload: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> Dict:
    """
    Build an error response dict.

    Args:
        reply: User-facing error message.
        payload: Optional error payload (e.g., ``{"error": str(e)}``).
        metadata: Optional metadata for debugging.

    Returns:
        Dict with keys: ``status`` (``"error"``), ``reply``, and optionally
        ``payload`` and ``metadata`` when they are not None.

    Example::

        return error("I couldn't determine the task name. Please try again.")
        return error("Failed to add task.", payload={"error": str(e)})
    """
    response: Dict = {"status": "error", "reply": reply}
    if payload is not None:
        response["payload"] = payload
    if metadata is not None:
        response["metadata"] = metadata
    return response


def partial(
    reply: str,
    payload: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> Dict:
    """
    Build a partial-success response dict.

    Use when an operation partially succeeded (e.g., some items processed,
    some failed).

    Args:
        reply: User-facing message describing the partial result.
        payload: Optional payload with details of what succeeded/failed.
        metadata: Optional metadata for debugging.

    Returns:
        Dict with keys: ``status`` (``"partial"``), ``reply``, and optionally
        ``payload`` and ``metadata`` when they are not None.

    Example::

        return partial(
            "Completed 2 tasks, but couldn't find 'invalid task'.",
            payload={"completed": [42, 43], "failed": ["invalid task"]},
        )
    """
    response: Dict = {"status": "partial", "reply": reply}
    if payload is not None:
        response["payload"] = payload
    if metadata is not None:
        response["metadata"] = metadata
    return response
