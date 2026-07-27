from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import copy
import json

@dataclass
class ExecutionContext:
    """Central data class carrying runtime state of the N.O.V.A. assistant.
    
    All fields have sensible defaults to support lazy initialization.
    """
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    last_command: Optional[str] = None
    last_intent: Optional[str] = None
    last_entities: Dict[str, Any] = field(default_factory=dict)
    last_result: Dict[str, Any] = field(default_factory=dict)
    
    current_application: Optional[str] = None
    current_window: Optional[str] = None
    current_browser: Optional[str] = None
    current_browser_tab: Optional[str] = None
    current_url: Optional[str] = None
    
    last_search_query: Optional[str] = None
    last_opened_application: Optional[str] = None
    last_closed_application: Optional[str] = None
    last_window_operation: Optional[str] = None
    last_volume_action: Optional[str] = None
    
    clipboard_text: Optional[str] = None
    selected_text: Optional[str] = None
    mouse_position: Optional[tuple] = None
    keyboard_modifiers: List[str] = field(default_factory=list)
    
    focused_element: Optional[str] = None
    focused_control: Optional[str] = None
    selected_file: Optional[str] = None
    selected_folder: Optional[str] = None
    recent_targets: List[str] = field(default_factory=list)
    
    conversation_state: Dict[str, Any] = field(default_factory=dict)
    active_task: Optional[str] = None
    active_chain: Optional[str] = None
    
    last_success: bool = True
    last_error: Optional[str] = None
    execution_timestamp: float = field(default_factory=time.time)
    
    # Bounded history list of dictionaries representing past successful/failed commands
    history: List[Dict[str, Any]] = field(default_factory=list)

    # Legacy fields for backwards compatibility with core/command_chain.py
    last_app: Optional[str] = None
    last_window: Optional[str] = None
    last_window_handle: Optional[int] = None
    last_website: Optional[str] = None

    # Properties to map rich fields to backwards-compatible fields
    @property
    def clipboard(self) -> Optional[str]:
        return self.clipboard_text

    @clipboard.setter
    def clipboard(self, value: Optional[str]) -> None:
        self.clipboard_text = value

    @property
    def current_selection(self) -> Optional[str]:
        return self.selected_text

    @current_selection.setter
    def current_selection(self, value: Optional[str]) -> None:
        self.selected_text = value

    @property
    def current_tab(self) -> Optional[str]:
        return self.current_browser_tab

    @current_tab.setter
    def current_tab(self, value: Optional[str]) -> None:
        self.current_browser_tab = value

    def snapshot(self) -> ExecutionContext:
        """Return an immutable snapshot copy of this context."""
        return copy.deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize current execution context into a dictionary."""
        return {
            "session_id": self.session_id,
            "request_id": self.request_id,
            "last_command": self.last_command,
            "last_intent": self.last_intent,
            "last_entities": self.last_entities,
            "last_result": self.last_result,
            "current_application": self.current_application,
            "current_window": self.current_window,
            "current_browser": self.current_browser,
            "current_browser_tab": self.current_browser_tab,
            "current_url": self.current_url,
            "last_search_query": self.last_search_query,
            "last_opened_application": self.last_opened_application,
            "last_closed_application": self.last_closed_application,
            "last_window_operation": self.last_window_operation,
            "last_volume_action": self.last_volume_action,
            "clipboard_text": self.clipboard_text,
            "selected_text": self.selected_text,
            "mouse_position": self.mouse_position,
            "keyboard_modifiers": self.keyboard_modifiers,
            "focused_element": self.focused_element,
            "focused_control": self.focused_control,
            "selected_file": self.selected_file,
            "selected_folder": self.selected_folder,
            "clipboard": self.clipboard,
            "current_tab": self.current_tab,
            "current_selection": self.current_selection,
            "recent_targets": self.recent_targets,
            "conversation_state": self.conversation_state,
            "active_task": self.active_task,
            "active_chain": self.active_chain,
            "last_success": self.last_success,
            "last_error": self.last_error,
            "execution_timestamp": self.execution_timestamp,
            "history": self.history,
            # Legacy mapping
            "last_app": self.last_app,
            "last_window": self.last_window,
            "last_window_handle": self.last_window_handle,
            "last_website": self.last_website,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ExecutionContext:
        """De-serialize dictionary into an ExecutionContext instance."""
        return cls(
            session_id=d.get("session_id"),
            request_id=d.get("request_id"),
            last_command=d.get("last_command"),
            last_intent=d.get("last_intent"),
            last_entities=d.get("last_entities", {}),
            last_result=d.get("last_result", {}),
            current_application=d.get("current_application"),
            current_window=d.get("current_window"),
            current_browser=d.get("current_browser"),
            current_browser_tab=d.get("current_browser_tab") or d.get("current_tab"),
            current_url=d.get("current_url"),
            last_search_query=d.get("last_search_query"),
            last_opened_application=d.get("last_opened_application"),
            last_closed_application=d.get("last_closed_application"),
            last_window_operation=d.get("last_window_operation"),
            last_volume_action=d.get("last_volume_action"),
            clipboard_text=d.get("clipboard_text") or d.get("clipboard"),
            selected_text=d.get("selected_text") or d.get("current_selection"),
            mouse_position=d.get("mouse_position"),
            keyboard_modifiers=d.get("keyboard_modifiers", []),
            focused_element=d.get("focused_element"),
            focused_control=d.get("focused_control"),
            selected_file=d.get("selected_file"),
            selected_folder=d.get("selected_folder"),
            recent_targets=d.get("recent_targets", []),
            conversation_state=d.get("conversation_state", {}),
            active_task=d.get("active_task"),
            active_chain=d.get("active_chain"),
            last_success=d.get("last_success", True),
            last_error=d.get("last_error"),
            execution_timestamp=d.get("execution_timestamp", time.time()),
            history=d.get("history", []),
            last_app=d.get("last_app"),
            last_window=d.get("last_window"),
            last_window_handle=d.get("last_window_handle"),
            last_website=d.get("last_website"),
        )

    def to_json(self) -> str:
        """Serialize current context into a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, s: str) -> ExecutionContext:
        """De-serialize JSON string into an ExecutionContext instance."""
        return cls.from_dict(json.loads(s))
