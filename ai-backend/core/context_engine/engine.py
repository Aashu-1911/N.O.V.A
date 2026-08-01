import threading
import copy
import time
import json
from typing import Dict, Any, Optional, List

from .dataclasses import (
    ResolvedWindow, ResolvedApplication, ResolvedBrowser, ResolvedFile,
    ResolvedClipboard, ResolvedTask, ResolvedPlanner, ResolvedConversation,
    ResolvedUI, ResolvedVision
)
from .events import ContextEvent, ContextEventDispatcher
from .snapshots import ContextSnapshot
from .history import ExecutionHistory, HistoryRecord

class ContextEngine:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(ContextEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._lock = threading.RLock()
        
        # Sub-contexts setup
        self.window = ResolvedWindow()
        self.application = ResolvedApplication()
        self.browser = ResolvedBrowser()
        self.file = ResolvedFile()
        self.clipboard = ResolvedClipboard()
        self.task = ResolvedTask()
        self.planner = ResolvedPlanner()
        self.conversation = ResolvedConversation()
        self.ui = ResolvedUI()
        self.vision = ResolvedVision()
        self.history = ExecutionHistory(max_size=500)
        self.dispatcher = ContextEventDispatcher()

        # Dynamic listener subscription
        self.dispatcher.subscribe("WINDOW_OPENED", self._on_window_opened)
        self.dispatcher.subscribe("WINDOW_CLOSED", self._on_window_closed)
        self.dispatcher.subscribe("WINDOW_FOCUSED", self._on_window_focused)
        self.dispatcher.subscribe("APPLICATION_STARTED", self._on_application_started)
        self.dispatcher.subscribe("APPLICATION_CLOSED", self._on_application_closed)
        self.dispatcher.subscribe("FILE_OPENED", self._on_file_opened)
        self.dispatcher.subscribe("TAB_CHANGED", self._on_tab_changed)
        self.dispatcher.subscribe("URL_OPENED", self._on_url_opened)
        self.dispatcher.subscribe("SEARCH_PERFORMED", self._on_search_performed)
        self.dispatcher.subscribe("TASK_COMPLETED", self._on_task_completed)
        self.dispatcher.subscribe("COMMAND_EXECUTED", self._on_command_executed)
        self.dispatcher.subscribe("COMMAND_FAILED", self._on_command_failed)
        self.dispatcher.subscribe("CLIPBOARD_CHANGED", self._on_clipboard_changed)
        self.dispatcher.subscribe("SELECTION_CHANGED", self._on_selection_changed)

        self._initialized = True

    def get_snapshot(self) -> ContextSnapshot:
        """Return a thread-safe deepcopy of the current context state."""
        with self._lock:
            return ContextSnapshot(
                window=copy.deepcopy(self.window),
                application=copy.deepcopy(self.application),
                browser=copy.deepcopy(self.browser),
                file=copy.deepcopy(self.file),
                clipboard=copy.deepcopy(self.clipboard),
                task=copy.deepcopy(self.task),
                planner=copy.deepcopy(self.planner),
                conversation=copy.deepcopy(self.conversation),
                ui=copy.deepcopy(self.ui),
                vision=copy.deepcopy(self.vision),
                timestamp=time.time()
            )

    def apply_snapshot(self, snapshot: ContextSnapshot) -> None:
        """Restore all sub-contexts from a given snapshot."""
        with self._lock:
            self.window = copy.deepcopy(snapshot.window)
            self.application = copy.deepcopy(snapshot.application)
            self.browser = copy.deepcopy(snapshot.browser)
            self.file = copy.deepcopy(snapshot.file)
            self.clipboard = copy.deepcopy(snapshot.clipboard)
            self.task = copy.deepcopy(snapshot.task)
            self.planner = copy.deepcopy(snapshot.planner)
            self.conversation = copy.deepcopy(snapshot.conversation)
            self.ui = copy.deepcopy(snapshot.ui)
            self.vision = copy.deepcopy(snapshot.vision)

    # Event handlers mutating sub-contexts
    def _on_window_opened(self, event: ContextEvent) -> None:
        with self._lock:
            hwnd = event.data.get("hwnd")
            title = event.data.get("title", "")
            self.window.window_history.append({"hwnd": hwnd, "title": title, "action": "open", "timestamp": event.timestamp})
            if hwnd and hwnd not in self.window.recent_windows_stack:
                self.window.recent_windows_stack.append(hwnd)

    def _on_window_closed(self, event: ContextEvent) -> None:
        with self._lock:
            hwnd = event.data.get("hwnd")
            self.window.window_history.append({"hwnd": hwnd, "action": "close", "timestamp": event.timestamp})
            if hwnd in self.window.recent_windows_stack:
                self.window.recent_windows_stack.remove(hwnd)
            if self.window.hwnd == hwnd:
                self.window.hwnd = None
                self.window.title = ""

    def _on_window_focused(self, event: ContextEvent) -> None:
        with self._lock:
            hwnd = event.data.get("window_handle") or event.data.get("hwnd")
            title = event.data.get("window_title") or event.data.get("title")
            op = event.data.get("operation", "focus")
            
            if hwnd:
                self.window.previous_window = self.window.hwnd
                self.window.hwnd = hwnd
                if hwnd in self.window.recent_windows_stack:
                    self.window.recent_windows_stack.remove(hwnd)
                self.window.recent_windows_stack.append(hwnd)
            if title:
                self.window.title = title
            self.window.focused = True
            self.window.last_operation = op
            self.window.timestamp = event.timestamp

    def _on_application_started(self, event: ContextEvent) -> None:
        with self._lock:
            app_name = event.data.get("app_name") or event.data.get("name")
            if app_name:
                self.application.last_opened_application = app_name
                if app_name not in self.application.running_applications:
                    self.application.running_applications.append(app_name)
                if app_name not in self.application.recently_used_applications:
                    self.application.recently_used_applications.append(app_name)
                self.application.foreground_application = app_name

    def _on_application_closed(self, event: ContextEvent) -> None:
        with self._lock:
            app_name = event.data.get("app_name") or event.data.get("name")
            if app_name:
                if app_name in self.application.running_applications:
                    self.application.running_applications.remove(app_name)
                if self.application.foreground_application == app_name:
                    self.application.foreground_application = None

    def _on_file_opened(self, event: ContextEvent) -> None:
        with self._lock:
            file_path = event.data.get("file_path") or event.data.get("path")
            if file_path:
                self.file.current_file = file_path
                if file_path not in self.file.opened_files:
                    self.file.opened_files.append(file_path)
                if file_path in self.file.recent_files:
                    self.file.recent_files.remove(file_path)
                self.file.recent_files.append(file_path)

    def _on_tab_changed(self, event: ContextEvent) -> None:
        with self._lock:
            tab = event.data.get("tab") or event.data.get("title")
            if tab:
                self.browser.previous_tab = self.browser.current_tab
                self.browser.current_tab = tab

    def _on_url_opened(self, event: ContextEvent) -> None:
        with self._lock:
            url = event.data.get("url")
            browser = event.data.get("browser", "Chrome")
            if url:
                self.browser.url = url
                self.browser.current_browser = browser
                self.browser.history.append(url)

    def _on_search_performed(self, event: ContextEvent) -> None:
        with self._lock:
            query = event.data.get("query")
            url = event.data.get("url")
            if query:
                self.browser.search_query = query
                self.browser.current_browser = event.data.get("browser", "Chrome")
                if url:
                    self.browser.url = url

    def _on_task_completed(self, event: ContextEvent) -> None:
        with self._lock:
            step = event.data.get("step")
            if step:
                if step in self.task.pending_steps:
                    self.task.pending_steps.remove(step)
                if step not in self.task.completed_steps:
                    self.task.completed_steps.append(step)

    def _on_command_executed(self, event: ContextEvent) -> None:
        with self._lock:
            rec = HistoryRecord(
                timestamp=event.timestamp,
                command=event.data.get("command", ""),
                intent=event.data.get("intent", ""),
                entities=event.data.get("entities", {}),
                handler=event.data.get("handler", ""),
                status="success",
                execution_time=event.data.get("execution_time", 0.0),
                parent_command=event.data.get("parent_command"),
                error_code=None,
                capability_used=event.data.get("capability"),
                verification_result=event.data.get("verification")
            )
            self.history.add(rec)
            
            # Sync with conversation working memory
            self.conversation.last_user_command = rec.command
            self.conversation.intent_history.append(rec.intent)
            self.conversation.entity_history.append(rec.entities)

    def _on_command_failed(self, event: ContextEvent) -> None:
        with self._lock:
            rec = HistoryRecord(
                timestamp=event.timestamp,
                command=event.data.get("command", ""),
                intent=event.data.get("intent", ""),
                entities=event.data.get("entities", {}),
                handler=event.data.get("handler", ""),
                status="error",
                execution_time=event.data.get("execution_time", 0.0),
                parent_command=event.data.get("parent_command"),
                error_code=event.data.get("error_code") or event.data.get("error"),
                capability_used=event.data.get("capability"),
                verification_result=event.data.get("verification")
            )
            self.history.add(rec)
            self.task.failures += 1

    def _on_clipboard_changed(self, event: ContextEvent) -> None:
        with self._lock:
            text = event.data.get("text")
            if text:
                self.clipboard.text = text
                self.clipboard.history.append(text)
                if len(self.clipboard.history) > 50:
                    self.clipboard.history.pop(0)

    def _on_selection_changed(self, event: ContextEvent) -> None:
        with self._lock:
            text = event.data.get("text")
            if text:
                self.ui.focused_control = event.data.get("control")
                self.ui.selected_text = text

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "window": self.window.__dict__,
                "application": self.application.__dict__,
                "browser": self.browser.__dict__,
                "file": self.file.__dict__,
                "clipboard": self.clipboard.__dict__,
                "task": self.task.__dict__,
                "planner": self.planner.__dict__,
                "conversation": self.conversation.__dict__,
                "ui": self.ui.__dict__,
                "vision": self.vision.__dict__,
                "history": self.history.to_list()
            }

    def dump(self) -> None:
        with self._lock:
            log_lines = [
                "=============================",
                "Context Engine",
                "=============================",
                f"Focused Window:   {self.window.title or 'None'}",
                f"HWND:             {self.window.hwnd or 'None'}",
                f"Current Browser:  {self.browser.current_browser or 'None'}",
                f"Current URL:      {self.browser.url or 'None'}",
                f"Current File:     {self.file.current_file or 'None'}",
                f"Current Task:     {self.task.goal or 'None'}",
                f"Execution Chain:  {len(self.task.completed_steps)}/{len(self.task.pending_steps) + len(self.task.completed_steps)}",
                f"Previous Window:  {self.window.previous_window or 'None'}",
                f"Recent Apps:      {', '.join(self.application.recently_used_applications[-4:]) or 'None'}",
                "============================="
            ]
            log_str = "\n".join(log_lines)
            print(log_str, flush=True)
