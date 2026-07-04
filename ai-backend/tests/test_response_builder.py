"""
Unit tests for core/response_builder.py

Tests success(), error(), and partial() factory functions.
Requirements: 5.5, 5.6
"""

import pytest
from core.response_builder import success, error, partial


# ---------------------------------------------------------------------------
# success()
# ---------------------------------------------------------------------------

class TestSuccess:
    def test_returns_dict(self):
        result = success("All done")
        assert isinstance(result, dict)

    def test_status_is_success(self):
        result = success("All done")
        assert result["status"] == "success"

    def test_reply_matches_input(self):
        result = success("Added task: learn Docker")
        assert result["reply"] == "Added task: learn Docker"

    def test_no_payload_by_default(self):
        result = success("OK")
        assert "payload" not in result

    def test_payload_included_when_provided(self):
        result = success("Done", payload={"task_id": 42})
        assert result["payload"] == {"task_id": 42}

    def test_no_metadata_by_default(self):
        result = success("OK")
        assert "metadata" not in result

    def test_metadata_included_when_provided(self):
        result = success("Done", metadata={"confidence": 0.9})
        assert result["metadata"] == {"confidence": 0.9}

    def test_both_payload_and_metadata(self):
        result = success("Done", payload={"id": 1}, metadata={"debug": True})
        assert result["payload"] == {"id": 1}
        assert result["metadata"] == {"debug": True}

    def test_empty_reply_string(self):
        result = success("")
        assert result["reply"] == ""
        assert result["status"] == "success"

    def test_payload_none_is_excluded(self):
        result = success("OK", payload=None)
        assert "payload" not in result

    def test_required_keys_present(self):
        result = success("hi")
        assert "status" in result
        assert "reply" in result


# ---------------------------------------------------------------------------
# error()
# ---------------------------------------------------------------------------

class TestError:
    def test_returns_dict(self):
        result = error("Something went wrong")
        assert isinstance(result, dict)

    def test_status_is_error(self):
        result = error("Something went wrong")
        assert result["status"] == "error"

    def test_reply_matches_input(self):
        result = error("Task not found")
        assert result["reply"] == "Task not found"

    def test_no_payload_by_default(self):
        result = error("Oops")
        assert "payload" not in result

    def test_payload_included_when_provided(self):
        result = error("Failed", payload={"error": "db timeout"})
        assert result["payload"] == {"error": "db timeout"}

    def test_no_metadata_by_default(self):
        result = error("Oops")
        assert "metadata" not in result

    def test_metadata_included_when_provided(self):
        result = error("Oops", metadata={"trace": "abc"})
        assert result["metadata"] == {"trace": "abc"}

    def test_payload_none_is_excluded(self):
        result = error("Oops", payload=None)
        assert "payload" not in result

    def test_required_keys_present(self):
        result = error("bad")
        assert "status" in result
        assert "reply" in result


# ---------------------------------------------------------------------------
# partial()
# ---------------------------------------------------------------------------

class TestPartial:
    def test_returns_dict(self):
        result = partial("Partially done")
        assert isinstance(result, dict)

    def test_status_is_partial(self):
        result = partial("Partially done")
        assert result["status"] == "partial"

    def test_reply_matches_input(self):
        result = partial("Completed 2, failed 1")
        assert result["reply"] == "Completed 2, failed 1"

    def test_no_payload_by_default(self):
        result = partial("Partial")
        assert "payload" not in result

    def test_payload_included_when_provided(self):
        result = partial("Done", payload={"completed": [1, 2], "failed": [3]})
        assert result["payload"] == {"completed": [1, 2], "failed": [3]}

    def test_no_metadata_by_default(self):
        result = partial("Partial")
        assert "metadata" not in result

    def test_metadata_included_when_provided(self):
        result = partial("Partial", metadata={"total": 3})
        assert result["metadata"] == {"total": 3}

    def test_payload_none_is_excluded(self):
        result = partial("Partial", payload=None)
        assert "payload" not in result

    def test_required_keys_present(self):
        result = partial("done-ish")
        assert "status" in result
        assert "reply" in result


# ---------------------------------------------------------------------------
# Cross-function: status value correctness
# ---------------------------------------------------------------------------

class TestStatusValues:
    def test_success_status_value(self):
        assert success("x")["status"] == "success"

    def test_error_status_value(self):
        assert error("x")["status"] == "error"

    def test_partial_status_value(self):
        assert partial("x")["status"] == "partial"

    def test_statuses_are_distinct(self):
        statuses = {success("x")["status"], error("x")["status"], partial("x")["status"]}
        assert len(statuses) == 3
