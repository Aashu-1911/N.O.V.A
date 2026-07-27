from dataclasses import dataclass
from typing import List, Optional

@dataclass
class WindowInfo:
    hwnd: int
    pid: int
    process_name: str
    executable_path: str
    title: str
    window_class: str
    monitor: int
    is_visible: bool
    is_foreground: bool
    is_minimized: bool
    is_maximized: bool
    is_cloaked: bool
    z_order: int
    creation_time: float
    capabilities: List[str]
    width: int = 0
    height: int = 0
