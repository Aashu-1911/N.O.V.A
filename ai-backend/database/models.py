from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskRecord:
    id: int
    task_name: str
    date: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    completed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None