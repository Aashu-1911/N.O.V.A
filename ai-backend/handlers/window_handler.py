"""
Window handlers — business logic for focus, maximize, minimize, restore,
list, and get-active-window intents.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from core.response_builder import error, success
from managers import window_manager

ResponseDict = Dict[str, Any]

_VERB_PAST = {
    "focus": "Focused",
    "maximize": "Maximized",
    "minimize": "Minimized",
    "restore": "Restored",
}


def _resolve_window(
    window_name: Optional[str],
    context: Optional[Dict[str, Any]],
) -> Optional[str]:
    if window_name:
        return window_name
    if context is not None:
        return context.get("last_window")
    return None


def _execute_window_action(
    action_name: str,
    manager_fn: Callable[[str], window_manager.WindowOperationResult],
    window_name: Optional[str],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    name = _resolve_window(window_name, context)

    if not name:
        return error("No window name provided.")

    try:
        result = manager_fn(name)

        if not result.success:
            reason = (result.reason or "").lower()
            if "not found" in reason:
                return error(f"Window '{name}' was not found.")
            return error(f"Unable to {action_name} window.")

        verb = _VERB_PAST.get(action_name, action_name.capitalize() + "d")
        return success(
            f"{verb} {result.matched_title}.",
            payload={
                "window_title": result.matched_title,
                "window_handle": result.handle,
            },
        )
    except Exception:
        return error(f"Unable to {action_name} window.")


def handle_focus_window(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    return _execute_window_action(
        "focus",
        window_manager.focus_window,
        entities.get("window_name"),
        context,
    )


def handle_maximize_window(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    return _execute_window_action(
        "maximize",
        window_manager.maximize_window,
        entities.get("window_name"),
        context,
    )


def handle_minimize_window(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    return _execute_window_action(
        "minimize",
        window_manager.minimize_window,
        entities.get("window_name"),
        context,
    )


def handle_restore_window(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    return _execute_window_action(
        "restore",
        window_manager.restore_window,
        entities.get("window_name"),
        context,
    )


def handle_list_windows(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    try:
        windows = window_manager.list_windows()
        if not windows:
            return success("No open windows found.", payload={"windows": []})
        count = len(windows)
        return success(
            f"There are {count} open windows.",
            payload={"windows": windows},
        )
    except Exception:
        return error("Unable to list windows.")


def handle_get_active_window(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    try:
        result = window_manager.get_active_window()

        if not result.success:
            return error("Unable to get active window.")

        if not result.matched_title:
            return success(
                "No active window detected.",
                payload={"window_title": None, "window_handle": None},
            )

        return success(
            f"Current active window is {result.matched_title}.",
            payload={
                "window_title": result.matched_title,
                "window_handle": result.handle,
                "process_name": result.process_name,
            },
        )
    except Exception:
        return error("Unable to get active window.")
