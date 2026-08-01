import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class HistoryRecord:
    timestamp: float
    command: str
    intent: str
    entities: Dict[str, Any]
    handler: str
    status: str
    execution_time: float
    parent_command: Optional[str] = None
    error_code: Optional[str] = None
    capability_used: Optional[str] = None
    verification_result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "command": self.command,
            "intent": self.intent,
            "entities": self.entities,
            "handler": self.handler,
            "status": self.status,
            "execution_time": self.execution_time,
            "parent_command": self.parent_command,
            "error_code": self.error_code,
            "capability_used": self.capability_used,
            "verification_result": self.verification_result
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'HistoryRecord':
        return cls(
            timestamp=d.get("timestamp", time.time()),
            command=d.get("command", ""),
            intent=d.get("intent", ""),
            entities=d.get("entities", {}),
            handler=d.get("handler", ""),
            status=d.get("status", ""),
            execution_time=d.get("execution_time", 0.0),
            parent_command=d.get("parent_command"),
            error_code=d.get("error_code"),
            capability_used=d.get("capability_used"),
            verification_result=d.get("verification_result")
        )

class ExecutionHistory:
    def __init__(self, max_size: int = 500) -> None:
        self.max_size = max_size
        self._records: List[HistoryRecord] = []
        self._intent_index: Dict[str, List[HistoryRecord]] = {}
        self._last_success: Optional[HistoryRecord] = None

    def add(self, record: HistoryRecord) -> None:
        self._records.append(record)
        
        if record.intent not in self._intent_index:
            self._intent_index[record.intent] = []
        self._intent_index[record.intent].append(record)
        
        if record.status == "success":
            self._last_success = record

        if len(self._records) > self.max_size:
            removed = self._records.pop(0)
            if removed.intent in self._intent_index:
                try:
                    self._intent_index[removed.intent].remove(removed)
                except ValueError:
                    pass

    def get_records(self) -> List[HistoryRecord]:
        return list(self._records)

    def get_by_intent(self, intent: str) -> List[HistoryRecord]:
        return list(self._intent_index.get(intent, []))

    def get_last_success(self) -> Optional[HistoryRecord]:
        return self._last_success

    def to_list(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._records]

    def from_list(self, data: List[Dict[str, Any]]) -> None:
        self._records = []
        self._intent_index = {}
        self._last_success = None
        for d in data:
            self.add(HistoryRecord.from_dict(d))
