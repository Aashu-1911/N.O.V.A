import copy
import time
from dataclasses import dataclass
from typing import Dict, Any
from .dataclasses import (
    ResolvedWindow, ResolvedApplication, ResolvedBrowser, ResolvedFile,
    ResolvedClipboard, ResolvedTask, ResolvedPlanner, ResolvedConversation,
    ResolvedUI, ResolvedVision
)

@dataclass
class ContextSnapshot:
    window: ResolvedWindow
    application: ResolvedApplication
    browser: ResolvedBrowser
    file: ResolvedFile
    clipboard: ResolvedClipboard
    task: ResolvedTask
    planner: ResolvedPlanner
    conversation: ResolvedConversation
    ui: ResolvedUI
    vision: ResolvedVision
    timestamp: float

def compute_snapshot_delta(before: ContextSnapshot, after: ContextSnapshot) -> Dict[str, Any]:
    """Compare before and after context snapshots and return a dict of differences."""
    delta = {}
    
    def check_diff(sub_name: str, before_obj, after_obj):
        diffs = {}
        for field_name in before_obj.__dataclass_fields__:
            b_val = getattr(before_obj, field_name)
            a_val = getattr(after_obj, field_name)
            if b_val != a_val:
                diffs[field_name] = {
                    "before": copy.deepcopy(b_val),
                    "after": copy.deepcopy(a_val)
                }
        if diffs:
            delta[sub_name] = diffs

    check_diff("window", before.window, after.window)
    check_diff("application", before.application, after.application)
    check_diff("browser", before.browser, after.browser)
    check_diff("file", before.file, after.file)
    check_diff("clipboard", before.clipboard, after.clipboard)
    check_diff("task", before.task, after.task)
    check_diff("planner", before.planner, after.planner)
    check_diff("conversation", before.conversation, after.conversation)
    check_diff("ui", before.ui, after.ui)
    check_diff("vision", before.vision, after.vision)
    
    return delta
