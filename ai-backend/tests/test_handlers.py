"""
Unit tests for handler modules.

Mocks all manager/service calls so no real I/O is performed.
Requirements: 5.2, 5.3
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# task_handler tests
# ---------------------------------------------------------------------------

class TestHandleAddTask:
    def test_success_returns_success_status(self):
        fake_task = {"id": 1, "task_name": "learn Docker", "completed": False}
        with patch("handlers.task_handler.add_task", return_value=fake_task):
            from handlers.task_handler import handle_add_task
            result = handle_add_task({"task_name": "learn Docker"})
        assert result["status"] == "success"

    def test_success_reply_contains_task_name(self):
        fake_task = {"id": 1, "task_name": "learn Docker", "completed": False}
        with patch("handlers.task_handler.add_task", return_value=fake_task):
            from handlers.task_handler import handle_add_task
            result = handle_add_task({"task_name": "learn Docker"})
        assert "learn Docker" in result["reply"]

    def test_success_payload_is_task(self):
        fake_task = {"id": 1, "task_name": "learn Docker", "completed": False}
        with patch("handlers.task_handler.add_task", return_value=fake_task):
            from handlers.task_handler import handle_add_task
            result = handle_add_task({"task_name": "learn Docker"})
        assert result["payload"] == fake_task

    def test_missing_task_name_returns_error(self):
        from handlers.task_handler import handle_add_task
        result = handle_add_task({})
        assert result["status"] == "error"

    def test_manager_exception_returns_error(self):
        with patch("handlers.task_handler.add_task", side_effect=Exception("DB error")):
            from handlers.task_handler import handle_add_task
            result = handle_add_task({"task_name": "fail task"})
        assert result["status"] == "error"


class TestHandleShowTasks:
    def test_success_with_tasks(self):
        fake_tasks = [
            {"id": 1, "task_name": "task one", "completed": False, "date": None},
            {"id": 2, "task_name": "task two", "completed": True, "date": None},
        ]
        with patch("handlers.task_handler.get_tasks", return_value=fake_tasks):
            from handlers.task_handler import handle_show_tasks
            result = handle_show_tasks({})
        assert result["status"] == "success"
        assert result["payload"]["tasks"] == fake_tasks

    def test_empty_task_list(self):
        with patch("handlers.task_handler.get_tasks", return_value=[]):
            from handlers.task_handler import handle_show_tasks
            result = handle_show_tasks({})
        assert result["status"] == "success"
        assert result["payload"]["tasks"] == []

    def test_manager_exception_returns_error(self):
        with patch("handlers.task_handler.get_tasks", side_effect=Exception("DB down")):
            from handlers.task_handler import handle_show_tasks
            result = handle_show_tasks({})
        assert result["status"] == "error"


class TestHandleCompleteTask:
    def test_success(self):
        fake_task = {"id": 1, "task_name": "learn Docker", "completed": True}
        with patch("handlers.task_handler.complete_task", return_value=fake_task):
            from handlers.task_handler import handle_complete_task
            result = handle_complete_task({"task_name": "learn Docker"})
        assert result["status"] == "success"
        assert result["payload"] == fake_task

    def test_task_not_found_returns_error(self):
        with patch("handlers.task_handler.complete_task", return_value=None):
            from handlers.task_handler import handle_complete_task
            result = handle_complete_task({"task_name": "missing"})
        assert result["status"] == "error"

    def test_missing_identifier_returns_error(self):
        from handlers.task_handler import handle_complete_task
        result = handle_complete_task({})
        assert result["status"] == "error"

    def test_manager_exception_returns_error(self):
        with patch("handlers.task_handler.complete_task", side_effect=Exception("fail")):
            from handlers.task_handler import handle_complete_task
            result = handle_complete_task({"task_name": "some task"})
        assert result["status"] == "error"


class TestHandleShowStats:
    def test_success(self):
        fake_stats = {"pending": 3, "completed": 7}
        with patch("handlers.task_handler.get_task_stats", return_value=fake_stats):
            from handlers.task_handler import handle_show_stats
            result = handle_show_stats({})
        assert result["status"] == "success"
        assert result["payload"] == fake_stats

    def test_reply_contains_counts(self):
        fake_stats = {"pending": 3, "completed": 7}
        with patch("handlers.task_handler.get_task_stats", return_value=fake_stats):
            from handlers.task_handler import handle_show_stats
            result = handle_show_stats({})
        assert "3" in result["reply"]
        assert "7" in result["reply"]

    def test_manager_exception_returns_error(self):
        with patch("handlers.task_handler.get_task_stats", side_effect=Exception("fail")):
            from handlers.task_handler import handle_show_stats
            result = handle_show_stats({})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# system_handler tests
# ---------------------------------------------------------------------------

class TestHandleLockPc:
    def test_success(self):
        with patch("handlers.system_handler.lock_pc") as mock_lock:
            from handlers.system_handler import handle_lock_pc
            result = handle_lock_pc({})
        assert result["status"] == "success"
        mock_lock.assert_called_once()

    def test_exception_returns_error(self):
        with patch("handlers.system_handler.lock_pc", side_effect=Exception("no perms")):
            from handlers.system_handler import handle_lock_pc
            result = handle_lock_pc({})
        assert result["status"] == "error"
        assert "payload" in result


class TestHandleScreenshot:
    def test_success_includes_filepath(self):
        with patch("handlers.system_handler.take_screenshot", return_value="/tmp/sc.png"):
            from handlers.system_handler import handle_screenshot
            result = handle_screenshot({})
        assert result["status"] == "success"
        assert result["payload"]["filepath"] == "/tmp/sc.png"

    def test_exception_returns_error(self):
        with patch("handlers.system_handler.take_screenshot", side_effect=Exception("err")):
            from handlers.system_handler import handle_screenshot
            result = handle_screenshot({})
        assert result["status"] == "error"


class TestHandleVolumeControl:
    @pytest.mark.parametrize("action,mock_fn", [
        ("mute",   "handlers.system_handler.mute_volume"),
        ("unmute", "handlers.system_handler.unmute_volume"),
        ("up",     "handlers.system_handler.volume_up"),
        ("down",   "handlers.system_handler.volume_down"),
    ])
    def test_valid_actions(self, action, mock_fn):
        with patch(mock_fn) as mock_call:
            from handlers.system_handler import handle_volume_control
            result = handle_volume_control({"volume_action": action})
        assert result["status"] == "success"
        mock_call.assert_called_once()

    def test_missing_action_returns_error(self):
        from handlers.system_handler import handle_volume_control
        result = handle_volume_control({})
        assert result["status"] == "error"

    def test_unknown_action_returns_error(self):
        from handlers.system_handler import handle_volume_control
        result = handle_volume_control({"volume_action": "louder_please"})
        assert result["status"] == "error"

    def test_exception_returns_error(self):
        with patch("handlers.system_handler.mute_volume", side_effect=Exception("hw error")):
            from handlers.system_handler import handle_volume_control
            result = handle_volume_control({"volume_action": "mute"})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# browser_handler tests
# ---------------------------------------------------------------------------

class TestHandleOpenWebsite:
    def test_success_with_url(self):
        with patch("handlers.browser_handler.open_website", return_value=True):
            from handlers.browser_handler import handle_open_website
            result = handle_open_website({"url": "github.com"})
        assert result["status"] == "success"

    def test_no_url_opens_default_browser(self):
        with patch("handlers.browser_handler.open_website", return_value=True):
            from handlers.browser_handler import handle_open_website
            result = handle_open_website({})
        assert result["status"] == "success"

    def test_open_website_returns_false_gives_error(self):
        with patch("handlers.browser_handler.open_website", return_value=False):
            from handlers.browser_handler import handle_open_website
            result = handle_open_website({"url": "github.com"})
        assert result["status"] == "error"

    def test_exception_returns_error(self):
        with patch("handlers.browser_handler.open_website", side_effect=Exception("no browser")):
            from handlers.browser_handler import handle_open_website
            result = handle_open_website({"url": "github.com"})
        assert result["status"] == "error"

    def test_uses_response_builder(self):
        """Success result must come from response_builder (has 'status' key)."""
        with patch("handlers.browser_handler.open_website", return_value=True):
            from handlers.browser_handler import handle_open_website
            result = handle_open_website({"url": "example.com"})
        assert "status" in result
        assert "reply" in result


class TestHandleSearchWeb:
    def test_success(self):
        with patch("handlers.browser_handler.open_website", return_value=True):
            from handlers.browser_handler import handle_search_web
            result = handle_search_web({"search_query": "python tutorials"})
        assert result["status"] == "success"
        assert "python tutorials" in result["reply"]

    def test_missing_query_returns_error(self):
        from handlers.browser_handler import handle_search_web
        result = handle_search_web({})
        assert result["status"] == "error"

    def test_open_website_returns_false_gives_error(self):
        with patch("handlers.browser_handler.open_website", return_value=False):
            from handlers.browser_handler import handle_search_web
            result = handle_search_web({"search_query": "weather"})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# app_handler tests
# ---------------------------------------------------------------------------

class TestHandleOpenApplication:
    def test_success(self):
        with patch("handlers.app_handler.open_application", return_value=True):
            from handlers.app_handler import handle_open_application
            result = handle_open_application({"app_name": "Notepad"})
        assert result["status"] == "success"
        assert "Notepad" in result["reply"]
        assert result["payload"]["app_name"] == "Notepad"

    def test_missing_app_name_returns_error(self):
        from handlers.app_handler import handle_open_application
        result = handle_open_application({})
        assert result["status"] == "error"

    def test_app_not_found_returns_error(self):
        with patch("handlers.app_handler.open_application", return_value=False):
            from handlers.app_handler import handle_open_application
            result = handle_open_application({"app_name": "GhostApp"})
        assert result["status"] == "error"

    def test_exception_returns_error(self):
        with patch("handlers.app_handler.open_application", side_effect=Exception("fail")):
            from handlers.app_handler import handle_open_application
            result = handle_open_application({"app_name": "Notepad"})
        assert result["status"] == "error"

    def test_uses_response_builder(self):
        with patch("handlers.app_handler.open_application", return_value=True):
            from handlers.app_handler import handle_open_application
            result = handle_open_application({"app_name": "Chrome"})
        assert "status" in result
        assert "reply" in result


class TestHandleCloseApplication:
    def test_success(self):
        with patch("handlers.app_handler.close_application", return_value=True):
            from handlers.app_handler import handle_close_application
            result = handle_close_application({"app_name": "Notepad"})
        assert result["status"] == "success"

    def test_missing_app_name_returns_error(self):
        from handlers.app_handler import handle_close_application
        result = handle_close_application({})
        assert result["status"] == "error"

    def test_app_not_found_returns_error(self):
        with patch("handlers.app_handler.close_application", return_value=False):
            from handlers.app_handler import handle_close_application
            result = handle_close_application({"app_name": "GhostApp"})
        assert result["status"] == "error"

    def test_exception_returns_error(self):
        with patch("handlers.app_handler.close_application", side_effect=Exception("fail")):
            from handlers.app_handler import handle_close_application
            result = handle_close_application({"app_name": "Notepad"})
        assert result["status"] == "error"
