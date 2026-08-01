from .dataclasses import (
    ResolvedWindow,
    ResolvedApplication,
    ResolvedBrowser,
    ResolvedFile,
    ResolvedClipboard,
    ResolvedTask,
    ResolvedPlanner,
    ResolvedConversation,
    ResolvedUI,
    ResolvedVision
)
from .events import ContextEvent, ContextEventDispatcher
from .snapshots import ContextSnapshot, compute_snapshot_delta
from .history import ExecutionHistory, HistoryRecord
from .engine import ContextEngine
from .resolver import ContextResolver

__all__ = [
    "ResolvedWindow",
    "ResolvedApplication",
    "ResolvedBrowser",
    "ResolvedFile",
    "ResolvedClipboard",
    "ResolvedTask",
    "ResolvedPlanner",
    "ResolvedConversation",
    "ResolvedUI",
    "ResolvedVision",
    "ContextEvent",
    "ContextEventDispatcher",
    "ContextSnapshot",
    "compute_snapshot_delta",
    "ExecutionHistory",
    "HistoryRecord",
    "ContextEngine",
    "ContextResolver",
]
