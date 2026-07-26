from dataclasses import dataclass
from typing import Optional, Union, Dict, Any
from automation.types import ControlType

@dataclass
class Selector:
    """Represents a set of criteria used to locate a UI element."""
    automation_id: Optional[str] = None
    name: Optional[str] = None
    partial_name: Optional[str] = None
    regex_name: Optional[str] = None
    class_name: Optional[str] = None
    control_type: Optional[Union[ControlType, str]] = None
    index: int = 0
    visible: Optional[bool] = None
    enabled: Optional[bool] = None
    focusable: Optional[bool] = None
    clickable: Optional[bool] = None
    depth: int = 0xFFFFFFFF
    search_scope: str = "descendants"  # "children" or "descendants"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the selector criteria to a dictionary format."""
        return {k: v for k, v in self.__dict__.items() if v is not None}
