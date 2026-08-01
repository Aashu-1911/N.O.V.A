from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

@dataclass
class ResolvedWindow:
    hwnd: Optional[int] = None
    pid: int = 0
    process_name: str = ""
    executable: str = ""
    title: str = ""
    monitor: int = 0
    visibility: bool = True
    minimized: bool = False
    maximized: bool = False
    focused: bool = False
    z_order: int = 0
    timestamp: float = 0.0
    last_operation: str = ""
    previous_window: Optional[int] = None
    recent_windows_stack: List[int] = field(default_factory=list)
    window_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ResolvedApplication:
    name: str = ""
    last_opened_application: Optional[str] = None
    running_applications: List[str] = field(default_factory=list)
    foreground_application: Optional[str] = None
    recently_used_applications: List[str] = field(default_factory=list)
    aliases: Dict[str, str] = field(default_factory=dict)
    exec_path: str = ""
    install_type: str = "unknown"

@dataclass
class ResolvedBrowser:
    current_browser: Optional[str] = None
    current_tab: Optional[str] = None
    previous_tab: Optional[str] = None
    url: Optional[str] = None
    history: List[str] = field(default_factory=list)
    search_query: Optional[str] = None
    downloads: List[str] = field(default_factory=list)

@dataclass
class ResolvedFile:
    current_folder: Optional[str] = None
    current_file: Optional[str] = None
    recent_files: List[str] = field(default_factory=list)
    opened_files: List[str] = field(default_factory=list)
    selected_file: Optional[str] = None
    explorer_window: Optional[str] = None

@dataclass
class ResolvedClipboard:
    text: Optional[str] = None
    image: Optional[str] = None  # path to cached image
    files: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)

@dataclass
class ResolvedTask:
    goal: str = ""
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    execution_chain: List[str] = field(default_factory=list)
    failures: int = 0
    retries: int = 0
    recovery_state: str = ""

@dataclass
class ResolvedPlanner:
    plan: List[Dict[str, Any]] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    current_execution_index: int = 0
    verification_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResolvedConversation:
    last_user_command: Optional[str] = None
    last_assistant_reply: Optional[str] = None
    intent_history: List[str] = field(default_factory=list)
    entity_history: List[Dict[str, Any]] = field(default_factory=list)
    recent_conversation: List[Dict[str, str]] = field(default_factory=list)
    clarifications: List[str] = field(default_factory=list)

@dataclass
class ResolvedUI:
    focused_control: Optional[str] = None
    hovered_element: Optional[str] = None
    selected_text: Optional[str] = None
    cursor_pos: Tuple[int, int] = (0, 0)
    scroll_pos: Tuple[int, int] = (0, 0)
    current_dialog: Optional[str] = None
    last_click: Optional[Tuple[int, int]] = None
    last_key_press: Optional[str] = None

@dataclass
class ResolvedVision:
    detected_windows: List[Dict[str, Any]] = field(default_factory=list)
    buttons: List[Dict[str, Any]] = field(default_factory=list)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    labels: List[Dict[str, Any]] = field(default_factory=list)
    bounding_boxes: List[Dict[str, Any]] = field(default_factory=list)
    icons: List[Dict[str, Any]] = field(default_factory=list)
    text_regions: List[Dict[str, Any]] = field(default_factory=list)
