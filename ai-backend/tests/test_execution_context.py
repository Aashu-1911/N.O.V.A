import time
import threading
import pytest
from core.execution_context import ExecutionContext
from core.context_manager import ExecutionContextManager
from core.context_events import ContextEvent
from core.command_executor import execute_command

def test_sensible_defaults():
    """Verify that an empty ExecutionContext has sensible defaults."""
    ec = ExecutionContext()
    assert ec.session_id is None
    assert ec.request_id is None
    assert ec.last_command is None
    assert ec.last_intent is None
    assert isinstance(ec.last_entities, dict)
    assert isinstance(ec.last_result, dict)
    assert ec.current_application is None
    assert ec.current_window is None
    assert ec.current_browser is None
    assert ec.current_url is None
    assert ec.last_search_query is None
    assert ec.last_opened_application is None
    assert ec.last_closed_application is None
    assert ec.last_volume_action is None
    assert ec.last_success is True
    assert ec.last_error is None
    assert isinstance(ec.history, list)
    assert len(ec.history) == 0


def test_application_updates(monkeypatch):
    """Verify that 'Open Chrome' updates the current application and last opened application."""
    monkeypatch.setattr("handlers.app_handler.open_application", lambda name: True)
    cm = ExecutionContextManager()
    
    result = execute_command("Open Chrome", context_manager=cm)
    
    assert result["status"] == "success"
    assert cm.get_current_application() == "chrome"
    
    snapshot = cm.get_snapshot()
    assert snapshot.current_application == "chrome"
    assert snapshot.last_opened_application == "chrome"
    assert snapshot.current_window == "chrome"
    assert snapshot.last_intent == "open_application"


def test_browser_updates(monkeypatch):
    """Verify that 'Search GitHub' updates search query, current browser and url."""
    monkeypatch.setattr("handlers.browser_handler.open_website", lambda url: True)
    cm = ExecutionContextManager()
    
    result = execute_command("Search GitHub", context_manager=cm)
    
    assert result["status"] == "success"
    assert cm.get_last_browser() == "Chrome"
    assert cm.get_last_search() == "GitHub"
    assert cm.get_last_url() is not None
    assert "github" in cm.get_last_url().lower()


def test_volume_updates(monkeypatch):
    """Verify that volume actions update last_volume_action."""
    monkeypatch.setattr("handlers.system_handler.mute_volume", lambda: None)
    cm = ExecutionContextManager()
    
    result = execute_command("Mute volume", context_manager=cm)
    assert cm.get_snapshot().last_volume_action == "mute"


def test_bounded_fifo_history():
    """Execute 150 commands and verify only the most recent 100 remain in FIFO history."""
    cm = ExecutionContextManager()
    
    # Run 150 commands (we manually trigger update_from_execution to save test time)
    for i in range(150):
        cmd = f"Test Command {i}"
        result = {"status": "success", "intent": "general_chat", "payload": {}}
        cm.update_from_execution(cmd, result, execution_time=0.01)
        
    history = cm.get_recent_history()
    assert len(history) == 100
    
    # Verify FIFO behavior: the oldest remaining command should be "Test Command 50"
    assert history[0]["command"] == "Test Command 50"
    assert history[-1]["command"] == "Test Command 149"


def test_thread_safety():
    """Spawn multiple threads updating context and verify no corruption or deadlocks."""
    cm = ExecutionContextManager()
    
    def worker(thread_idx: int):
        for i in range(50):
            cmd = f"Thread {thread_idx} Cmd {i}"
            result = {"status": "success", "intent": "general_chat", "payload": {}}
            cm.update_from_execution(cmd, result)
            snapshot = cm.get_snapshot()
            assert snapshot is not None
            assert isinstance(snapshot.last_command, str)

    threads = []
    for t_idx in range(5):
        t = threading.Thread(target=worker, args=(t_idx,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=5.0)

    # Total entries added: 250. Bounded history size should cap at 100.
    history = cm.get_recent_history()
    assert len(history) == 100
    assert any("Thread" in entry["command"] for entry in history)


def test_serialization():
    """Serialize and deserialize context state and verify equality."""
    cm = ExecutionContextManager()
    
    cm.update_from_execution("Open Chrome", {"status": "success", "intent": "open_application", "payload": {"app_name": "Chrome"}})
    cm.update_from_execution("Search GitHub", {"status": "success", "intent": "search_web", "payload": {"query": "GitHub", "url": "https://github.com"}})
    
    json_str = cm.to_json()
    
    cm2 = ExecutionContextManager()
    cm2.from_json(json_str)
    
    snap1 = cm.get_snapshot()
    snap2 = cm2.get_snapshot()
    
    assert snap1.to_dict() == snap2.to_dict()


def test_snapshot_immutability():
    """Verify that mutating a snapshot does not affect the live context."""
    cm = ExecutionContextManager()
    cm.update_from_execution("Open Chrome", {"status": "success", "intent": "open_application", "payload": {"app_name": "chrome"}})
    
    snapshot = cm.get_snapshot()
    assert snapshot.current_application == "chrome"
    
    # Mutate snapshot
    snapshot.current_application = "Firefox"
    snapshot.last_entities = {"mutated": "entities"}
    
    # Check that live context is unaffected
    assert cm.get_current_application() == "chrome"
    assert cm.get_snapshot().current_application == "chrome"
    assert cm.get_snapshot().last_entities.get("app_name") == "chrome"
    assert cm.get_snapshot().last_entities.get("mutated") is None


def test_failure_recovery():
    """Verify failed commands update last_error but preserve previous successful state."""
    cm = ExecutionContextManager()
    
    # 1. Establish successful state
    cm.update_from_execution("Open Chrome", {"status": "success", "intent": "open_application", "payload": {"app_name": "chrome"}})
    assert cm.get_current_application() == "chrome"
    assert cm.get_snapshot().last_success is True
    assert cm.get_snapshot().last_error is None
    
    # 2. Simulate failed command
    fail_res = {
        "status": "error",
        "intent": "open_website",
        "payload": {"error": "Connection timed out"},
        "reply": "I failed to open the website."
    }
    cm.update_from_failure("Open missingwebsite.com", fail_res)
    
    # 3. Check failure and preservation of previous state
    snap = cm.get_snapshot()
    assert snap.last_command == "Open missingwebsite.com"
    assert snap.last_intent == "open_website"
    assert snap.last_success is False
    assert snap.last_error == "Connection timed out"
    
    # Previous state (current_application == "chrome") must be preserved
    assert snap.current_application == "chrome"


def test_pronoun_resolution(monkeypatch):
    """Verify that 'Close it' resolves 'it' to the currently open application (telegram)."""
    monkeypatch.setattr("handlers.app_handler.open_application", lambda name: True)
    monkeypatch.setattr("handlers.app_handler.close_application", lambda name: True)
    cm = ExecutionContextManager()
    
    # 1. Open Telegram to establish open app context
    execute_command("Open Telegram", context_manager=cm)
    assert cm.get_current_application() == "telegram"
    
    # 2. Run "Close it" which should close telegram
    result = execute_command("Close it", context_manager=cm)
    assert result["status"] == "success"
    assert result["intent"] == "close_application"
    assert cm.get_current_application() is None


def test_repeat_action(monkeypatch):
    """Verify that repeat keywords like 'Do it again' repeats the previous command."""
    monkeypatch.setattr("handlers.system_handler.mute_volume", lambda: None)
    cm = ExecutionContextManager()
    
    # 1. Execute mute volume
    execute_command("Mute volume", context_manager=cm)
    assert cm.get_snapshot().last_volume_action == "mute"
    
    # Reset volume action in current state to see it repeat
    cm._context.last_volume_action = None
    
    # 2. Execute repeat
    execute_command("Do it again", context_manager=cm)
    assert cm.get_snapshot().last_volume_action == "mute"


def test_search_context_resolution(monkeypatch):
    """Verify that 'Open first result' resolves using the last search query context."""
    monkeypatch.setattr("handlers.browser_handler.open_website", lambda url: True)
    cm = ExecutionContextManager()
    
    # 1. Run a search
    execute_command("Search GitHub", context_manager=cm)
    assert cm.get_last_search() == "GitHub"
    
    # 2. Run 'Open the first result'
    result = execute_command("Open the first result", context_manager=cm)
    assert result["status"] == "success"
    assert result["payload"].get("url") == "https://github.com"


def test_context_queries(monkeypatch):
    """Verify that contextual queries return status='success' and correct textual answers."""
    monkeypatch.setattr("handlers.app_handler.open_application", lambda name: True)
    monkeypatch.setattr("handlers.browser_handler.open_website", lambda url: True)
    cm = ExecutionContextManager()
    
    # Open Chrome
    execute_command("Open Chrome", context_manager=cm)
    
    # Open github.com
    execute_command("Open github.com", context_manager=cm)
    
    # Query: What website am I on?
    res1 = execute_command("What website am I on?", context_manager=cm)
    assert res1["status"] == "success"
    assert "github.com" in res1["reply"].lower()
    
    # Query: What application is open?
    res2 = execute_command("What application is open?", context_manager=cm)
    assert res2["status"] == "success"
    assert "chrome" in res2["reply"].lower()


def test_parent_command_history():
    """Verify that chained commands map to the parent_command in FIFO history."""
    cm = ExecutionContextManager()
    
    execute_command("Hello, how are you?", context_manager=cm)
    
    history = cm.get_recent_history()
    # "Hello, how are you?" is split into ["Hello", "how are you?"]
    assert len(history) >= 2
    
    for entry in history:
        assert entry["parent_command"] == "Hello, how are you?"


def test_implicit_close(monkeypatch):
    """Verify that 'Close' without specifying an app closes the current active application."""
    monkeypatch.setattr("handlers.app_handler.open_application", lambda name: True)
    monkeypatch.setattr("handlers.app_handler.close_application", lambda name: True)
    cm = ExecutionContextManager()
    
    # 1. Open Telegram to make it active app
    execute_command("Open Telegram", context_manager=cm)
    assert cm.get_current_application() == "telegram"
    
    # 2. Run "Close" (no app name)
    result = execute_command("Close", context_manager=cm)
    assert result["status"] == "success"
    assert result["intent"] == "close_application"
    assert cm.get_current_application() is None


def test_remove_synonym(monkeypatch):
    """Verify that 'remove calculator' is correctly mapped to close_application intent."""
    monkeypatch.setattr("handlers.app_handler.close_application", lambda name: True)
    cm = ExecutionContextManager()
    
    result = execute_command("remove calculator", context_manager=cm)
    assert result["status"] == "success"
    assert result["intent"] == "close_application"
    assert cm.get_snapshot().last_entities.get("app_name") == "calculator"


def test_refresh_browser(monkeypatch):
    """Verify that 'Refresh' maps to browser_refresh intent when browser context exists."""
    monkeypatch.setattr("handlers.browser_handler.open_website", lambda url: True)
    cm = ExecutionContextManager()
    
    # Establish browser context
    execute_command("Open google.com", context_manager=cm)
    assert cm.get_snapshot().current_browser == "Chrome"
    
    # Run Refresh
    result = execute_command("Refresh", context_manager=cm)
    assert result["status"] == "success"
    assert result["intent"] == "browser_refresh"


def test_search_again(monkeypatch):
    """Verify that 'Search again' repeats the last search query."""
    monkeypatch.setattr("handlers.browser_handler.open_website", lambda url: True)
    cm = ExecutionContextManager()
    
    # Execute search
    execute_command("Search OpenAI", context_manager=cm)
    assert cm.get_last_search() == "OpenAI"
    
    # Run Search again
    result = execute_command("Search again", context_manager=cm)
    assert result["status"] == "success"
    assert result["intent"] == "search_web"
    assert result["reply"] == "Searching for OpenAI"


def test_close_empty_context():
    """Verify 'Close' with empty context expects clarification response."""
    cm = ExecutionContextManager()
    
    result = execute_command("Close", context_manager=cm)
    assert result["status"] == "success"
    assert result["reply"] == "Which application would you like me to close?"
    assert result["payload"].get("error") == "missing_context"


def test_open_it_again(monkeypatch):
    """Verify 'Open it again' opens the last_opened_application."""
    monkeypatch.setattr("handlers.app_handler.open_application", lambda name: True)
    monkeypatch.setattr("handlers.app_handler.close_application", lambda name: True)
    cm = ExecutionContextManager()
    
    # Open Telegram
    execute_command("Open Telegram", context_manager=cm)
    assert cm.get_snapshot().last_opened_application == "telegram"
    
    # Close it
    execute_command("Close it", context_manager=cm)
    assert cm.get_current_application() is None
    
    # Open it again
    result = execute_command("Open it again", context_manager=cm)
    assert result["status"] == "success"
    assert result["intent"] == "open_application"
    assert cm.get_current_application() == "telegram"


def test_minimize_restore_it(monkeypatch):
    """Verify pronoun resolution for window operations 'Minimize it' and 'Restore it'."""
    monkeypatch.setattr("handlers.app_handler.open_application", lambda name: True)
    
    from collections import namedtuple
    WindowOperationResult = namedtuple("WindowOperationResult", ["success", "matched_title", "handle", "reason"])
    
    monkeypatch.setattr(
        "managers.window_manager.minimize_window",
        lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None)
    )
    monkeypatch.setattr(
        "managers.window_manager.restore_window",
        lambda name: WindowOperationResult(success=True, matched_title=name, handle=123, reason=None)
    )
    
    cm = ExecutionContextManager()
    
    execute_command("Open Telegram", context_manager=cm)
    
    # Minimize it
    res1 = execute_command("Minimize it", context_manager=cm)
    assert res1["status"] == "success"
    assert res1["intent"] == "minimize_window"
    assert cm.get_snapshot().last_window_operation == "minimize"
    
    # Restore it
    res2 = execute_command("Restore it", context_manager=cm)
    assert res2["status"] == "success"
    assert res2["intent"] == "restore_window"
    assert cm.get_snapshot().last_window_operation == "restore"



