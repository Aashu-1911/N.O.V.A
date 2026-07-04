"""
Task handlers - handles add_task, show_tasks, complete_task, show_stats intents.
"""

from typing import Dict, Optional

from core.response_builder import success, error
from managers.task_manager import add_task, complete_task, get_tasks, get_task_stats


def handle_add_task(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for add_task intent."""
    task_name = entities.get("task_name")

    if not task_name:
        return error("I couldn't determine the task name. Please try again.")

    try:
        task = add_task(
            task_name=task_name,
            date=entities.get("date"),
            category=entities.get("category"),
            priority=entities.get("priority")
        )
        return success(f"Added task: {task_name}", payload=task)
    except Exception as e:
        return error(f"Failed to add task: {str(e)}", payload={"error": str(e)})


def handle_show_tasks(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for show_tasks intent."""
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


def handle_complete_task(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for complete_task intent."""
    task_identifier = entities.get("task_name") or entities.get("task_id")

    if not task_identifier:
        return error("I couldn't determine which task to complete. Please specify the task name or ID.")

    try:
        task = complete_task(task_identifier)

        if not task:
            return error(f"Task '{task_identifier}' not found.")

        return success(f"Completed task: {task['task_name']}", payload=task)
    except Exception as e:
        return error(f"Failed to complete task: {str(e)}", payload={"error": str(e)})


def handle_show_stats(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for show_stats intent."""
    try:
        stats = get_task_stats()
        reply = f"You have {stats['pending']} pending and {stats['completed']} completed tasks."
        return success(reply, payload=stats)
    except Exception as e:
        return error("Failed to get task statistics.", payload={"error": str(e)})


def handle_update_task(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler stub for update_task intent."""
    return success("Handler not implemented yet - update_task")
