import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from core.execution_context import ExecutionContext
from core.context_history import ContextHistory, HistoryEntry
from core.context_events import ContextEventDispatcher, ContextEvent
from core.context_engine.engine import ContextEngine

logger = logging.getLogger(__name__)

class ExecutionContextManager:
    def __init__(self, max_history_size: int = 100) -> None:
        self._lock = threading.RLock()
        self._context = ExecutionContext()
        self._history = ContextHistory(max_size=max_history_size)
        self._dispatcher = ContextEventDispatcher()
        self._engine = ContextEngine()

    # Query APIs
    def get_current_application(self) -> Optional[str]:
        with self._lock:
            return self._context.current_application

    def get_last_command(self) -> Optional[str]:
        with self._lock:
            return self._context.last_command

    def get_last_intent(self) -> Optional[str]:
        with self._lock:
            return self._context.last_intent

    def get_last_window(self) -> Optional[str]:
        with self._lock:
            return self._context.current_window

    def get_last_browser(self) -> Optional[str]:
        with self._lock:
            return self._context.current_browser

    def get_last_search(self) -> Optional[str]:
        with self._lock:
            return self._context.last_search_query

    def get_last_url(self) -> Optional[str]:
        with self._lock:
            return self._context.current_url

    def get_recent_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return self._history.to_list()

    def get_snapshot(self) -> ExecutionContext:
        with self._lock:
            return self._context.snapshot()

    # Event system subscription
    def subscribe_to_event(self, event_name: str, callback: Callable[[ContextEvent], None]) -> None:
        self._dispatcher.subscribe(event_name, callback)

    def unsubscribe_from_event(self, event_name: str, callback: Callable[[ContextEvent], None]) -> None:
        self._dispatcher.unsubscribe(event_name, callback)

    def update_from_execution(
        self,
        command: str,
        result: Dict[str, Any],
        execution_time: float = 0.0,
        parent_command: Optional[str] = None,
        context_updates: Optional[Dict[str, Any]] = None,
        entities: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update context and history state after a successful command execution."""
        with self._lock:
            status = result.get("status", "success")
            intent = result.get("intent", "unknown")
            payload = result.get("payload") or {}

            # Use passed entities if available, otherwise fallback to parse_intent
            if entities is None:
                from core.intent_parser import parse_intent
                try:
                    parsed = parse_intent(command)
                    entities = parsed.get("entities") or {}
                except Exception:
                    entities = {}

            # Update common context fields
            self._context.last_command = command
            self._context.last_intent = intent
            self._context.last_entities = entities
            self._context.last_result = result
            self._context.last_success = True
            self._context.last_error = None
            self._context.execution_timestamp = time.time()

            # Track recent targets automatically
            target_val = entities.get("app_name") or entities.get("window_name") or entities.get("url") or entities.get("search_query") or entities.get("title") or entities.get("control_name") or entities.get("source")
            if target_val:
                if not self._context.recent_targets:
                    self._context.recent_targets = []
                if target_val in self._context.recent_targets:
                    self._context.recent_targets.remove(target_val)
                self._context.recent_targets.append(target_val)
                if len(self._context.recent_targets) > 10:
                    self._context.recent_targets.pop(0)

            # Apply explicit context updates if supplied (new capability model)
            if context_updates is not None:
                for k, v in context_updates.items():
                    if hasattr(self._context, k):
                        setattr(self._context, k, v)
                
                # Dispatch events based on updates
                if "current_application" in context_updates and context_updates["current_application"]:
                    self._dispatcher.dispatch("APPLICATION_OPENED", {"app_name": context_updates["current_application"]})
                if "last_closed_application" in context_updates and context_updates["last_closed_application"]:
                    self._dispatcher.dispatch("APPLICATION_CLOSED", {"app_name": context_updates["last_closed_application"]})
                if "current_url" in context_updates and context_updates["current_url"]:
                    self._dispatcher.dispatch("URL_OPENED", {"url": context_updates["current_url"]})
                if "last_search_query" in context_updates and context_updates["last_search_query"]:
                    self._dispatcher.dispatch("SEARCH_PERFORMED", {"query": context_updates["last_search_query"], "url": context_updates.get("current_url")})
                if "last_volume_action" in context_updates and context_updates["last_volume_action"]:
                    self._dispatcher.dispatch("VOLUME_CHANGED", {"action": context_updates["last_volume_action"]})
                if "current_window" in context_updates and context_updates["current_window"]:
                    self._dispatcher.dispatch("WINDOW_FOCUSED", {"window_title": context_updates["current_window"], "operation": context_updates.get("last_window_operation", "focus")})
            else:
                # Legacy updates path
                if intent == "open_application":
                    app_name = entities.get("app_name") or payload.get("app_name")
                    if app_name:
                        self._context.current_application = app_name
                        self._context.last_opened_application = app_name
                        self._context.current_window = app_name
                        self._context.last_app = app_name
                        self._context.last_window = app_name
                        self._dispatcher.dispatch("APPLICATION_OPENED", {"app_name": app_name})
                
                elif intent == "close_application":
                    app_name = entities.get("app_name") or payload.get("app_name")
                    if app_name:
                        self._context.last_closed_application = app_name
                        if self._context.current_application == app_name:
                            self._context.current_application = None
                            self._context.current_window = None
                        self._dispatcher.dispatch("APPLICATION_CLOSED", {"app_name": app_name})

                elif intent == "open_website":
                    url = payload.get("url") or entities.get("url")
                    if url:
                        self._context.current_url = url
                        self._context.last_website = url
                        self._context.current_browser = "Chrome"
                        self._dispatcher.dispatch("URL_OPENED", {"url": url})

                elif intent == "search_web":
                    query = entities.get("search_query") or payload.get("query")
                    url = payload.get("url")
                    if query:
                        self._context.last_search_query = query
                        self._context.current_browser = "Chrome"
                        if url:
                            self._context.current_url = url
                        self._dispatcher.dispatch("SEARCH_PERFORMED", {"query": query, "url": url})

                elif intent == "volume_control":
                    action = entities.get("volume_action") or payload.get("action")
                    if action:
                        self._context.last_volume_action = action
                        self._dispatcher.dispatch("VOLUME_CHANGED", {"action": action})

                elif intent in ["focus_window", "maximize_window", "minimize_window", "restore_window"]:
                    op = intent.replace("_window", "")
                    self._context.last_window_operation = op
                    window_title = payload.get("window_title")
                    window_handle = payload.get("window_handle")
                    if window_title:
                        self._context.current_window = window_title
                        self._context.last_window = window_title
                    if window_handle:
                        self._context.last_window_handle = window_handle
                    self._dispatcher.dispatch("WINDOW_FOCUSED", {"window_title": window_title, "operation": op})

            # Record handler execution info into bounded history
            from core.command_executor import HANDLERS
            handler_func = HANDLERS.get(intent)
            handler_name = handler_func.__name__ if handler_func else "handle_general_chat"

            entry = HistoryEntry(
                timestamp=self._context.execution_timestamp,
                command=command,
                intent=intent,
                entities=entities,
                handler=handler_name,
                status=status,
                execution_time=execution_time,
                parent_command=parent_command
            )
            self._history.add(entry)
            self._context.history = self._history.to_list()

            # Reset temporary fields
            self._context.request_id = None
            
            # Log and event firing
            self._log_context_update()

            # Sync events to ContextEngine
            self._engine.dispatcher.dispatch("COMMAND_EXECUTED", {
                "command": command,
                "intent": intent,
                "entities": entities,
                "handler": handler_name,
                "execution_time": execution_time,
                "parent_command": parent_command
            })
            
            if target_val:
                if intent == "open_application":
                    self._engine.dispatcher.dispatch("APPLICATION_STARTED", {"app_name": target_val})
                elif intent == "close_application":
                    self._engine.dispatcher.dispatch("APPLICATION_CLOSED", {"app_name": target_val})
                elif intent == "open_website":
                    self._engine.dispatcher.dispatch("URL_OPENED", {"url": target_val})
                elif intent == "search_web":
                    self._engine.dispatcher.dispatch("SEARCH_PERFORMED", {"query": target_val})
                elif intent in ["focus_window", "maximize_window", "minimize_window", "restore_window"]:
                    self._engine.dispatcher.dispatch("WINDOW_FOCUSED", {
                        "window_handle": payload.get("window_handle"),
                        "window_title": payload.get("window_title"),
                        "operation": intent.replace("_window", "")
                    })

    def update_from_failure(
        self,
        command: str,
        result: Dict[str, Any],
        execution_time: float = 0.0,
        parent_command: Optional[str] = None,
    ) -> None:
        """Update context and history state after a failed command execution."""
        with self._lock:
            error_msg = result.get("payload", {}).get("error") or result.get("reply") or "Unknown error"
            intent = result.get("intent", "unknown")

            from core.intent_parser import parse_intent
            try:
                parsed = parse_intent(command)
                entities = parsed.get("entities") or {}
            except Exception:
                entities = {}

            # Update fail state but preserve previous successful settings
            self._context.last_command = command
            self._context.last_intent = intent
            self._context.last_entities = entities
            self._context.last_result = result
            self._context.last_success = False
            self._context.last_error = error_msg
            self._context.execution_timestamp = time.time()

            from core.command_executor import HANDLERS
            handler_func = HANDLERS.get(intent)
            handler_name = handler_func.__name__ if handler_func else "unknown"

            entry = HistoryEntry(
                timestamp=self._context.execution_timestamp,
                command=command,
                intent=intent,
                entities=entities,
                handler=handler_name,
                status="error",
                execution_time=execution_time,
                parent_command=parent_command
            )
            self._history.add(entry)
            self._context.history = self._history.to_list()

            self._dispatcher.dispatch("COMMAND_FAILED", {"command": command, "error": error_msg})
            self._context.request_id = None

            self._log_context_update()

            # Sync failure to ContextEngine
            self._engine.dispatcher.dispatch("COMMAND_FAILED", {
                "command": command,
                "intent": intent,
                "entities": entities,
                "handler": handler_name,
                "execution_time": execution_time,
                "parent_command": parent_command,
                "error": error_msg
            })

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "context": self._context.to_dict(),
                "history": self._history.to_list()
            }

    def from_dict(self, data: Dict[str, Any]) -> None:
        with self._lock:
            if "context" in data:
                self._context = ExecutionContext.from_dict(data["context"])
            if "history" in data:
                self._history.from_list(data["history"])

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    def from_json(self, s: str) -> None:
        import json
        self.from_dict(json.loads(s))

    def _log_context_update(self) -> None:
        log_lines = [
            "============================",
            "Execution Context Updated",
            f"Intent:       {self._context.last_intent}",
            f"Command:      {self._context.last_command}",
            f"Application:  {self._context.current_application}",
            f"Browser:      {self._context.current_browser}",
            f"Window:       {self._context.current_window}",
            f"URL:          {self._context.current_url}",
            f"Search Query: {self._context.last_search_query}",
            f"History Size: {len(self._history.get_entries())}",
            f"Timestamp:    {self._context.execution_timestamp}",
            "============================"
        ]
        log_str = "\n".join(log_lines)
        logger.info(log_str)
        print(log_str, flush=True)

    def dump(self) -> None:
        with self._lock:
            print("\n==========================", flush=True)
            print("EXECUTION CONTEXT DUMP", flush=True)
            print("==========================", flush=True)
            for k, v in self._context.to_dict().items():
                print(f"{k}: {v}", flush=True)
            print(f"history_size: {len(self._history.get_entries())}", flush=True)
            print("==========================\n", flush=True)
