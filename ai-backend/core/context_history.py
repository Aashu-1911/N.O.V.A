import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class HistoryEntry:
    timestamp: float
    command: str
    intent: str
    entities: Dict[str, Any]
    handler: str
    status: str
    execution_time: float
    parent_command: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "command": self.command,
            "intent": self.intent,
            "entities": self.entities,
            "handler": self.handler,
            "status": self.status,
            "execution_time": self.execution_time,
            "parent_command": self.parent_command
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'HistoryEntry':
        return cls(
            timestamp=d.get("timestamp", time.time()),
            command=d.get("command", ""),
            intent=d.get("intent", ""),
            entities=d.get("entities", {}),
            handler=d.get("handler", ""),
            status=d.get("status", ""),
            execution_time=d.get("execution_time", 0.0),
            parent_command=d.get("parent_command")
        )

class ContextHistory:
    def __init__(self, max_size: int = 100) -> None:
        self.max_size = max_size
        self._entries: List[HistoryEntry] = []

    def add(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self.max_size:
            self._entries.pop(0)

    def get_entries(self) -> List[HistoryEntry]:
        return list(self._entries)

    def to_list(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def from_list(self, data: List[Dict[str, Any]]) -> None:
        self._entries = [HistoryEntry.from_dict(d) for d in data]
        if len(self._entries) > self.max_size:
            self._entries = self._entries[-self.max_size:]
