import time
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Callable

@dataclass
class ContextEvent:
    name: str
    data: Dict[str, Any]
    timestamp: float

class ContextEventDispatcher:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[ContextEvent], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_name: str, callback: Callable[[ContextEvent], None]) -> None:
        with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[ContextEvent], None]) -> None:
        with self._lock:
            if event_name in self._listeners:
                try:
                    self._listeners[event_name].remove(callback)
                except ValueError:
                    pass

    def dispatch(self, event_name: str, data: Dict[str, Any]) -> None:
        event = ContextEvent(
            name=event_name,
            data=data,
            timestamp=time.time()
        )
        with self._lock:
            listeners = list(self._listeners.get(event_name, []))
            listeners.extend(self._listeners.get("*", []))

        for callback in listeners:
            try:
                callback(event)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error in context engine event callback: {e}")
