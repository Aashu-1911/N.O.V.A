from typing import Any, Dict, List
from capabilities.base import BaseCapability, ParsedCommand
from capabilities.response import CapabilityResponse

class FileSystemCapability(BaseCapability):
    """Subsystem capability representing File System interaction."""

    @property
    def name(self) -> str:
        return "FileSystemCapability"

    def priority(self) -> int:
        return 50

    @property
    def supported_verbs(self) -> List[str]:
        return ["open", "delete", "create", "list", "copy"]

    @property
    def supported_objects(self) -> List[str]:
        return ["file", "folder", "directory", "files"]

    def confidence(self, parsed: ParsedCommand, context: Dict[str, Any]) -> float:
        obj_lower = (parsed.object or "").lower()
        if parsed.verb in self.supported_verbs:
            if any(ind in obj_lower for ind in self.supported_objects):
                return 1.0
            
            # Explicit filenames/paths check
            if "/" in obj_lower or "\\" in obj_lower or "." in obj_lower:
                # Avoid web URL open check
                if "http" not in obj_lower and parsed.verb != "open":
                    return 1.0

        return 0.0

    def health(self) -> bool:
        return True

    def execute(self, parsed: ParsedCommand, context: Dict[str, Any]) -> CapabilityResponse:
        interpretation = f"FileSystem action: '{parsed.verb}' on path '{parsed.object}'"
        return CapabilityResponse(
            status="success",
            reply="File system capability not implemented.",
            payload={
                "interpretation": interpretation,
                "execution_summary": "Skipped (FileSystem not implemented)"
            },
            verification_result=True
        )
