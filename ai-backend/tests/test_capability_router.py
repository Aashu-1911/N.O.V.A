import pytest
from core.command_executor import execute_command
from core.context_manager import ExecutionContextManager

def test_capability_routing(monkeypatch):
    """Verify that routing decisions are routed to correct capabilities deterministically."""
    # 1. Mock handlers to avoid real OS/UI changes
    monkeypatch.setattr("handlers.browser_handler.handle_open_website", lambda ent, ctx: {"status": "success", "reply": "mocked website"})
    monkeypatch.setattr("handlers.browser_handler.handle_search_web", lambda ent, ctx: {"status": "success", "reply": "mocked search"})
    monkeypatch.setattr("handlers.app_handler.handle_open_application", lambda ent, ctx=None: {"status": "success", "reply": f"Opening {ent.get('app_name')}."})
    monkeypatch.setattr("handlers.app_handler.handle_close_application", lambda ent, ctx=None: {"status": "success", "reply": f"Closing {ent.get('app_name')}."})
    monkeypatch.setattr("handlers.system_handler.handle_volume_control", lambda ent, ctx: {"status": "success", "reply": "mocked volume"})
    monkeypatch.setattr("handlers.media_handler.handle_media_control", lambda ent, ctx: {"status": "success", "reply": "mocked media"})
    monkeypatch.setattr("handlers.chat_handler.handle_general_chat", lambda ent, ctx: {"status": "success", "reply": "mocked chat response"})
    
    from collections import namedtuple
    WindowOperationResult = namedtuple("WindowOperationResult", ["success", "matched_title", "handle", "reason"])
    monkeypatch.setattr("managers.window_manager.focus_window", lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None))
    monkeypatch.setattr("managers.window_manager.minimize_window", lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None))

    cm = ExecutionContextManager()

    # Test Browser open
    res = execute_command("Open google.com", context_manager=cm)
    assert res["handled_by"] == "BrowserCapability"

    # Test Application launch
    res = execute_command("Open Calculator", context_manager=cm)
    assert res["handled_by"] == "WindowCapability"

    # Test Window close it
    assert cm.get_current_application() == "calculator"
    res = execute_command("Close it", context_manager=cm)
    assert res["handled_by"] == "WindowCapability"

    # Test Search web
    res = execute_command("Search Python", context_manager=cm)
    assert res["handled_by"] == "BrowserCapability"

    # Test UI Automation find button placeholder
    res = execute_command("Find Save button", context_manager=cm)
    assert res["handled_by"] == "UIAutomationCapability"
    assert "not yet implemented" in res["reply"]

    # Test UI Automation list controls placeholder
    res = execute_command("List controls", context_manager=cm)
    assert res["handled_by"] == "UIAutomationCapability"

    # Test Vision placeholder
    res = execute_command("Read screen", context_manager=cm)
    assert res["handled_by"] == "VisionCapability"
    assert "not implemented" in res["reply"]

    # Test OCR placeholder
    res = execute_command("Extract text", context_manager=cm)
    assert res["handled_by"] == "OCRCapability"
    assert "not implemented" in res["reply"]

    # Test General LLM fallback
    res = execute_command("Explain recursion", context_manager=cm)
    assert res["handled_by"] == "GeneralLLMCapability"

    # Test Volume control
    res = execute_command("Increase volume", context_manager=cm)
    assert res["handled_by"] == "VolumeCapability"

    # Test Media playback
    res = execute_command("Pause music", context_manager=cm)
    assert res["handled_by"] == "MediaCapability"
