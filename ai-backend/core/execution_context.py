"""
execution_context.py — Shared state carrier for chained command execution.

This module defines the ExecutionContext dataclass, which is passed between
sub-commands in a chain so that resolved references (last opened app, last
visited website, etc.) are available to subsequent commands without using
global variables.

IMPORT CONSTRAINT: This module intentionally imports ONLY from the Python
standard library (`dataclasses` and `typing`). It must NEVER import from
`core.command_executor`, `core.command_chain`, or any other project module.
This keeps ExecutionContext at the bottom of the dependency graph and
prevents any circular import issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionContext:
    """Carries shared state between sub-commands in a chained execution.

    Initialised fresh at the start of every top-level execute_chain() call.
    Fields are updated after each sub-command completes so that later
    sub-commands can resolve pronouns ("it", "this app") and implicit
    references to the last opened application or website.

    Fields:
        last_app:     Name of the most recently opened application, or None.
        last_window:  Window title proxy for the most recently opened app, or None.
        last_website: URL of the most recently opened website, or None.
        last_command: Raw text of the most recently executed sub-command, or None.
        last_intent:  Intent string of the most recently executed sub-command
                      (not updated for skipped sub-commands), or None.
    """

    last_app: Optional[str] = None
    last_window: Optional[str] = None
    last_window_handle: Optional[int] = None
    last_website: Optional[str] = None
    last_command: Optional[str] = None
    last_intent: Optional[str] = None
