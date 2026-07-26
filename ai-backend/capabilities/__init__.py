from capabilities.base import BaseCapability, ParsedCommand
from capabilities.response import CapabilityResponse
from capabilities.parser import CommandParser
from capabilities.registry import register_capability, get_registered_capabilities
from capabilities.router import CapabilityRouter

# Import all capabilities to ensure they are loaded
from capabilities.window import WindowCapability
from capabilities.browser import BrowserCapability
from capabilities.files import FileSystemCapability
from capabilities.media import MediaCapability
from capabilities.volume import VolumeCapability
from capabilities.conversation import ConversationCapability
from capabilities.general_llm import GeneralLLMCapability, ClipboardCapability, SystemCapability, TaskManagementCapability
from capabilities.ui_automation import UIAutomationCapability
from capabilities.vision import VisionCapability
from capabilities.ocr import OCRCapability

# Register singletons of standard capabilities
register_capability(WindowCapability())
register_capability(BrowserCapability())
register_capability(FileSystemCapability())
register_capability(MediaCapability())
register_capability(VolumeCapability())
register_capability(ConversationCapability())
register_capability(GeneralLLMCapability())
register_capability(ClipboardCapability())
register_capability(SystemCapability())
register_capability(TaskManagementCapability())
register_capability(UIAutomationCapability())
register_capability(VisionCapability())
register_capability(OCRCapability())

__all__ = [
    "BaseCapability",
    "ParsedCommand",
    "CapabilityResponse",
    "CommandParser",
    "CapabilityRouter",
    "register_capability",
    "get_registered_capabilities"
]
