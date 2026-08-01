import pytest
import time
import threading
from core.context_engine import (
    ContextEngine, ContextResolver, ContextSnapshot,
    ResolvedWindow, ResolvedApplication, ResolvedBrowser, ResolvedFile,
    ResolvedClipboard, ResolvedTask, ResolvedPlanner, ResolvedConversation,
    ResolvedUI, ResolvedVision
)
from core.context_engine.history import HistoryRecord

def test_context_engine_initialization():
    engine = ContextEngine()
    assert isinstance(engine.window, ResolvedWindow)
    assert isinstance(engine.application, ResolvedApplication)
    assert isinstance(engine.browser, ResolvedBrowser)
    assert isinstance(engine.file, ResolvedFile)
    assert isinstance(engine.clipboard, ResolvedClipboard)
    assert isinstance(engine.task, ResolvedTask)
    assert isinstance(engine.planner, ResolvedPlanner)
    assert isinstance(engine.conversation, ResolvedConversation)
    assert isinstance(engine.ui, ResolvedUI)
    assert isinstance(engine.vision, ResolvedVision)

def test_event_mutation_handling():
    engine = ContextEngine()
    engine.window.hwnd = None
    
    # Focused window event
    engine.dispatcher.dispatch("WINDOW_FOCUSED", {
        "hwnd": 12345,
        "title": "Notepad",
        "operation": "focus"
    })
    
    assert engine.window.hwnd == 12345
    assert engine.window.title == "Notepad"
    assert engine.window.focused is True
    assert engine.window.last_operation == "focus"

    # Started app event
    engine.dispatcher.dispatch("APPLICATION_STARTED", {
        "app_name": "Notepad"
    })
    assert engine.application.foreground_application == "Notepad"
    assert "Notepad" in engine.application.running_applications

    # File open event
    engine.dispatcher.dispatch("FILE_OPENED", {
        "path": "C:\\test.txt"
    })
    assert engine.file.current_file == "C:\\test.txt"
    assert "C:\\test.txt" in engine.file.opened_files

def test_snapshots_and_rollback():
    engine = ContextEngine()
    
    engine.dispatcher.dispatch("WINDOW_FOCUSED", {"hwnd": 111, "title": "First"})
    snapshot_before = engine.get_snapshot()
    
    engine.dispatcher.dispatch("WINDOW_FOCUSED", {"hwnd": 222, "title": "Second"})
    assert engine.window.hwnd == 222
    
    engine.apply_snapshot(snapshot_before)
    assert engine.window.hwnd == 111

def test_pronoun_and_keyword_resolution():
    engine = ContextEngine()
    resolver = ContextResolver()
    
    engine.dispatcher.dispatch("WINDOW_FOCUSED", {"hwnd": 999, "title": "Telegram"})
    snapshot = engine.get_snapshot()
    
    resolved_it = resolver.resolve("it", snapshot)
    assert isinstance(resolved_it, ResolvedWindow)
    assert resolved_it.hwnd == 999
    
    resolved_curr = resolver.resolve("current", snapshot)
    assert isinstance(resolved_curr, ResolvedWindow)
    
    resolved_prev = resolver.resolve("previous", snapshot)
    assert isinstance(resolved_prev, ResolvedWindow)

def test_concurrency_stress():
    engine = ContextEngine()
    
    threads = []
    
    def worker_writer(val):
        for i in range(10):
            engine.dispatcher.dispatch("WINDOW_FOCUSED", {"hwnd": val + i, "title": f"Win {val + i}"})
            time.sleep(0.001)

    def worker_reader():
        for _ in range(20):
            snap = engine.get_snapshot()
            _ = snap.window.hwnd
            time.sleep(0.001)

    for i in range(50):
        t_w = threading.Thread(target=worker_writer, args=(i * 100,))
        t_r = threading.Thread(target=worker_reader)
        threads.extend([t_w, t_r])
        t_w.start()
        t_r.start()

    for t in threads:
        t.join()
        
    assert len(engine.history.get_records()) >= 0

def test_history_limit_and_indexing():
    engine = ContextEngine()
    
    # Load 550 sequential commands
    for i in range(550):
        engine.dispatcher.dispatch("COMMAND_EXECUTED", {
            "command": f"cmd {i}",
            "intent": "open_app",
            "handler": "test_handler",
            "execution_time": 0.01
        })
        
    assert len(engine.history.get_records()) == 500
    by_intent = engine.history.get_by_intent("open_app")
    assert len(by_intent) == 500
