import pytest
from capabilities.base import (
    WindowReference, BrowserReference, FileReference, TextBoxReference,
    UIElementReference, OCRTarget, VisionTarget
)
from core.context_resolver import ContextResolver
from capabilities.parser import CommandParser
from core.execution_context import ExecutionContext

def test_semantic_reference_resolution(monkeypatch):
    """Verifies that referring expressions resolve to concrete Reference classes based on priority context."""
    from collections import namedtuple
    WindowOperationResult = namedtuple("WindowOperationResult", ["success", "matched_title", "handle", "reason"])
    monkeypatch.setattr("managers.window_manager.focus_window", lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None))
    monkeypatch.setattr("managers.window_manager.minimize_window", lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None))
    monkeypatch.setattr("managers.window_manager.restore_window", lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None))

    resolver = ContextResolver()

    # 1. Open Notepad -> Minimize it -> WindowReference(Notepad)
    ctx1 = ExecutionContext()
    ctx1.current_application = "Notepad"
    ctx1.current_window = "Notepad"
    
    parsed1 = CommandParser.parse("Minimize it")
    resolved1 = resolver.resolve(parsed1, ctx1)
    assert isinstance(resolved1.target, WindowReference)
    assert resolved1.target.window_name == "Notepad"

    # 2. Open Chrome -> Refresh it -> BrowserReference(Chrome)
    ctx2 = ExecutionContext()
    ctx2.current_browser = "Chrome"
    
    parsed2 = CommandParser.parse("Refresh it")
    resolved2 = resolver.resolve(parsed2, ctx2)
    assert isinstance(resolved2.target, BrowserReference)
    assert resolved2.target.browser_name == "Chrome"

    # 3. Focus VS Code -> Close current window -> WindowReference(VS Code)
    ctx3 = ExecutionContext()
    ctx3.current_window = "VS Code"
    
    parsed3 = CommandParser.parse("Close current window")
    resolved3 = resolver.resolve(parsed3, ctx3)
    assert isinstance(resolved3.target, WindowReference)
    assert resolved3.target.window_name == "VS Code"

    # 4. Select report.pdf -> Delete it -> FileReference(report.pdf)
    ctx4 = ExecutionContext()
    ctx4.selected_file = "report.pdf"
    
    parsed4 = CommandParser.parse("Delete it")
    resolved4 = resolver.resolve(parsed4, ctx4)
    assert isinstance(resolved4.target, FileReference)
    assert resolved4.target.file_path == "report.pdf"

    # 5. Focus Username textbox -> Type hello -> Focused TextBox (TextBoxReference)
    ctx5 = ExecutionContext()
    ctx5.focused_element = "Username textbox"
    
    parsed5 = CommandParser.parse("Type hello")
    resolved5 = resolver.resolve(parsed5, ctx5)
    assert isinstance(resolved5.target, TextBoxReference)

    # 6. Click Save -> UIElementReference("Save")
    parsed6 = CommandParser.parse("Click Save")
    # Resolution should preserve Click Save as UIElementReference
    resolved6 = resolver.resolve(parsed6, ExecutionContext())
    assert isinstance(resolved6.target, UIElementReference)
    assert resolved6.target.element_name == "Save"

    # 7. Read it (after OCR) -> OCR Result (OCRTarget)
    ctx7 = ExecutionContext()
    # Mocking OCR last state
    ctx7.last_intent = "ocr_extract"
    parsed7 = CommandParser.parse("Read it")
    resolved7 = resolver.resolve(parsed7, ctx7)
    assert isinstance(resolved7.target, OCRTarget)

    # 8. Describe it (after Vision) -> Captured Screen (VisionTarget)
    ctx8 = ExecutionContext()
    ctx8.last_intent = "describe_screen"
    parsed8 = CommandParser.parse("Describe it")
    resolved8 = resolver.resolve(parsed8, ctx8)
    assert isinstance(resolved8.target, VisionTarget)
