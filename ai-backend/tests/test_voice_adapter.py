"""
Integration tests for voice_adapter.py — voice command flow.

Tests that voice_command_callback:
  - Calls execute_command with the received text
  - Calls speak() with the reply from the response dict
  - Handles error status and empty replies gracefully
  - Does not crash when speak() itself raises

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

import pytest
from unittest.mock import patch, MagicMock, call


# Patch targets as used inside voice_adapter.py
SPEAK_PATH = "adapters.voice_adapter.speak"
EXECUTE_PATH = "adapters.voice_adapter.execute_command"


class TestVoiceCommandCallbackDispatch:
    """voice_command_callback must call execute_command with the received text."""

    def test_calls_execute_command_with_text(self):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done"}) as mock_exec, \
             patch(SPEAK_PATH):
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("add task learn Docker")
        mock_exec.assert_called_once_with("add task learn Docker")

    def test_empty_string_does_not_call_execute_command(self):
        with patch(EXECUTE_PATH) as mock_exec, patch(SPEAK_PATH):
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("")
        mock_exec.assert_not_called()

    def test_whitespace_only_does_not_call_execute_command(self):
        with patch(EXECUTE_PATH) as mock_exec, patch(SPEAK_PATH):
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("   ")
        mock_exec.assert_not_called()


class TestVoiceCommandCallbackSpeak:
    """speak() must be called with the reply extracted from the response dict."""

    def test_speak_called_with_reply(self):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "All done"}), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("some command")
        mock_speak.assert_called_once()
        spoken = mock_speak.call_args[0][0]
        assert "All done" in spoken

    def test_speak_called_once_per_command(self):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done"}), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("open browser")
        assert mock_speak.call_count == 1

    def test_speak_receives_string(self):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Ready"}), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("ready check")
        spoken = mock_speak.call_args[0][0]
        assert isinstance(spoken, str)

    def test_markdown_stripped_before_speak(self):
        """format_for_voice should remove markdown markers like **bold**."""
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "**Done** with *style*"}), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("some command")
        spoken = mock_speak.call_args[0][0]
        assert "**" not in spoken
        assert "*" not in spoken

    def test_empty_reply_triggers_fallback_speak(self):
        """An empty reply should still call speak() with a fallback message."""
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": ""}), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("anything")
        mock_speak.assert_called_once()


class TestVoiceCommandCallbackErrorHandling:
    """Error status and exceptions must be handled; speak() must still be called."""

    def test_error_status_still_calls_speak(self):
        with patch(EXECUTE_PATH, return_value={"status": "error", "reply": "Something failed"}), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("bad command")
        mock_speak.assert_called_once()

    def test_execute_command_exception_calls_speak_with_error_msg(self):
        with patch(EXECUTE_PATH, side_effect=Exception("Unexpected crash")), \
             patch(SPEAK_PATH) as mock_speak:
            from adapters.voice_adapter import voice_command_callback
            voice_command_callback("boom")
        mock_speak.assert_called_once()
        spoken = mock_speak.call_args[0][0]
        assert isinstance(spoken, str)
        assert len(spoken) > 0

    def test_speak_failure_does_not_propagate(self):
        """If speak() itself raises, voice_command_callback must not raise."""
        with patch(EXECUTE_PATH, side_effect=Exception("crash")), \
             patch(SPEAK_PATH, side_effect=Exception("TTS broken")):
            from adapters.voice_adapter import voice_command_callback
            # Should not raise
            voice_command_callback("trigger error path")


# ---------------------------------------------------------------------------
# format_for_voice helper tests
# ---------------------------------------------------------------------------

class TestFormatForVoice:
    def test_removes_bold(self):
        from adapters.voice_adapter import format_for_voice
        assert "**" not in format_for_voice("**bold text**")

    def test_removes_italic(self):
        from adapters.voice_adapter import format_for_voice
        result = format_for_voice("*italic*")
        assert "*" not in result

    def test_removes_inline_code(self):
        from adapters.voice_adapter import format_for_voice
        result = format_for_voice("use `pip install` command")
        assert "`" not in result
        assert "pip install" in result

    def test_removes_fenced_code_block(self):
        from adapters.voice_adapter import format_for_voice
        result = format_for_voice("```python\nprint('hi')\n```")
        assert "```" not in result

    def test_removes_heading_markers(self):
        from adapters.voice_adapter import format_for_voice
        result = format_for_voice("# Heading One")
        assert "#" not in result
        assert "Heading One" in result

    def test_plain_text_unchanged(self):
        from adapters.voice_adapter import format_for_voice
        text = "Hello, this is plain text."
        assert format_for_voice(text) == text

    def test_returns_string(self):
        from adapters.voice_adapter import format_for_voice
        assert isinstance(format_for_voice("anything"), str)
