"""
Task handlers - handles add_task, show_tasks, complete_task, show_stats, update_task intents.

All functions in this module accept an ``entities`` dict (extracted by the intent parser)
and an optional ``context`` dict (carries session state, the raw command string, etc.).
They return a ``ResponseDict`` built with :mod:`core.response_builder` helpers.

This module has NO voice imports and NO HTTP framework imports.
"""

from typing import Any, Dict, Optional

from core.response_builder import success, error
from managers.task_manager import add_task, complete_task, get_tasks, get_task_stats

# Convenience alias for the structured response dict returned by every handler.
ResponseDict = Dict[str, Any]


def handle_add_task(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``add_task`` intent — create a new task.

    Args:
        entities: Intent entities extracted by the parser.  Expected keys:

            - ``task_name`` *(str, required)* — name of the task to create.
            - ``date`` *(str, optional)* — due date string (e.g. ``"2024-02-01"``).
            - ``category`` *(str, optional)* — task category label.
            - ``priority`` *(str, optional)* — ``"low"``, ``"medium"``, or ``"high"``.

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and the created task object in
        ``payload``, or ``status="error"`` with a human-readable ``reply``.

    Example::

        result = handle_add_task({"task_name": "learn Docker", "priority": "high"})
        # {"status": "success", "reply": "Added task: learn Docker", "payload": {...}}
    """
    task_name = entities.get("task_name")

    if not task_name:
        return error("I couldn't determine the task name. Please try again.")

    try:
        task = add_task(
            task_name=task_name,
            date=entities.get("date"),
            category=entities.get("category"),
            priority=entities.get("priority"),
        )
        return success(f"Added task: {task_name}", payload=task)
    except Exception as e:
        return error(f"Failed to add task: {str(e)}", payload={"error": str(e)})


def handle_show_tasks(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``show_tasks`` intent — list pending (and optionally completed) tasks.

    Args:
        entities: Intent entities.  Expected keys:

            - ``include_completed`` *(bool, optional, default False)* — when ``True``,
              completed tasks are included in the listing.

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with a human-readable task list in ``reply`` and the raw
        task list in ``payload["tasks"]``.  Returns an empty-list success when
        there are no tasks.

    Example::

        result = handle_show_tasks({})
        # {"status": "success", "reply": "Here are your tasks:\\n○ learn Docker", "payload": {"tasks": [...]}}
    """
    try:
        include_completed = entities.get("include_completed", False)
        tasks = get_tasks(include_completed=include_completed)

        if not tasks:
            return success("You have no tasks.", payload={"tasks": []})

        task_list = []
        for task in tasks:
            status_icon = "✓" if task["completed"] else "○"
            task_str = f"{status_icon} {task['task_name']}"
            if task.get("date"):
                task_str += f" (due: {task['date']})"
            task_list.append(task_str)

        reply = "Here are your tasks:\n" + "\n".join(task_list)
        return success(reply, payload={"tasks": tasks})
    except Exception as e:
        return error("Failed to fetch tasks.", payload={"error": str(e)})


def handle_complete_task(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``complete_task`` intent — mark a task as done.

    Args:
        entities: Intent entities.  At least one of the following must be present:

            - ``task_name`` *(str)* — name of the task to complete.
            - ``task_id`` *(int | str)* — numeric ID of the task to complete.

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and the updated task in ``payload``,
        or ``status="error"`` if the task was not found or the identifier is missing.

    Example::

        result = handle_complete_task({"task_name": "learn Docker"})
        # {"status": "success", "reply": "Completed task: learn Docker", "payload": {...}}
    """
    task_identifier = entities.get("task_name") or entities.get("task_id")

    if not task_identifier:
        return error(
            "I couldn't determine which task to complete. "
            "Please specify the task name or ID."
        )

    try:
        task = complete_task(task_identifier)

        if not task:
            return error(f"Task '{task_identifier}' not found.")

        return success(f"Completed task: {task['task_name']}", payload=task)
    except Exception as e:
        return error(f"Failed to complete task: {str(e)}", payload={"error": str(e)})


def handle_show_stats(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``show_stats`` intent — summarise pending vs. completed task counts.

    Args:
        entities: Intent entities (not used by this handler).
        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"``, a human-readable summary in ``reply``,
        and the full stats dict in ``payload``.

    Example::

        result = handle_show_stats({})
        # {"status": "success", "reply": "You have 3 pending and 7 completed tasks.", "payload": {...}}
    """
    try:
        stats = get_task_stats()
        reply = (
            f"You have {stats['pending']} pending and {stats['completed']} completed tasks."
        )
        return success(reply, payload=stats)
    except Exception as e:
        return error("Failed to get task statistics.", payload={"error": str(e)})


def handle_update_task(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Stub handler for the ``update_task`` intent (not yet implemented).

    Args:
        entities: Intent entities (ignored by stub).
        context: Optional session / request context (ignored by stub).

    Returns:
        ResponseDict with ``status="success"`` and a placeholder reply indicating
        the handler is not yet implemented.

    Example::

        result = handle_update_task({"task_name": "learn Docker"})
        # {"status": "success", "reply": "Handler not implemented yet - update_task"}
    """
    return success("Handler not implemented yet - update_task")
