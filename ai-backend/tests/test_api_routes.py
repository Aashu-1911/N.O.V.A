"""
Integration tests for API route flow (api/routes.py).

Uses FastAPI TestClient to call the HTTP endpoints and verifies that:
  - /execute calls execute_command and returns JSON
  - Response dict is serialized correctly
  - Error responses return correct HTTP status

Requirements: 10.3, 10.6, 10.7
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Patch target as used inside api/routes.py
EXECUTE_PATH = "api.routes.execute_command"


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app without triggering startup events."""
    from main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# /execute endpoint
# ---------------------------------------------------------------------------

class TestExecuteEndpoint:
    def test_calls_execute_command_with_message(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done", "intent": "add_task"}) as mock_exec:
            client.post("/execute", json={"message": "add task learn Docker"})
        mock_exec.assert_called_once_with("add task learn Docker")

    def test_returns_200_on_success(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done", "intent": "add_task"}):
            response = client.post("/execute", json={"message": "add task learn Docker"})
        assert response.status_code == 200

    def test_response_is_json(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done", "intent": "add_task"}):
            response = client.post("/execute", json={"message": "anything"})
        # FastAPI should serialize the dict as JSON
        assert response.headers["content-type"].startswith("application/json")

    def test_response_contains_status(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done", "intent": "add_task"}):
            response = client.post("/execute", json={"message": "anything"})
        body = response.json()
        assert "status" in body

    def test_response_contains_reply(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Task added", "intent": "add_task"}):
            response = client.post("/execute", json={"message": "add task"})
        body = response.json()
        assert body["reply"] == "Task added"

    def test_response_serializes_payload(self, client):
        fake = {
            "status": "success",
            "reply": "Here are your tasks",
            "payload": {"tasks": [{"id": 1, "task_name": "test", "completed": False}]},
            "intent": "show_tasks",
        }
        with patch(EXECUTE_PATH, return_value=fake):
            response = client.post("/execute", json={"message": "show tasks"})
        body = response.json()
        assert body["payload"]["tasks"][0]["task_name"] == "test"

    def test_error_response_serialized(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "error", "reply": "Something went wrong", "intent": "unknown"}):
            response = client.post("/execute", json={"message": "bad command"})
        assert response.status_code == 200  # route returns 200 even for logic errors
        body = response.json()
        assert body["status"] == "error"
        assert body["reply"] == "Something went wrong"

    def test_missing_message_returns_422(self, client):
        """Pydantic validation should reject requests missing 'message'."""
        response = client.post("/execute", json={})
        assert response.status_code == 422

    def test_task_id_optional(self, client):
        """task_id field is optional in TaskActionRequest."""
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Done", "intent": "add_task"}):
            response = client.post("/execute", json={"message": "add task", "task_id": 5})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /chat endpoint (backward compatibility wrapper)
# ---------------------------------------------------------------------------

class TestChatEndpoint:
    def test_chat_calls_execute_command(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Hi there", "intent": "general_chat"}) as mock_exec:
            client.post("/chat", json={"message": "how are you?"})
        mock_exec.assert_called_once_with("how are you?")

    def test_chat_returns_200(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Hi", "intent": "general_chat"}):
            response = client.post("/chat", json={"message": "hello"})
        assert response.status_code == 200

    def test_chat_response_is_json(self, client):
        with patch(EXECUTE_PATH, return_value={"status": "success", "reply": "Hi", "intent": "general_chat"}):
            response = client.post("/chat", json={"message": "hello"})
        assert response.headers["content-type"].startswith("application/json")

    def test_chat_missing_message_returns_422(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# / health check
# ---------------------------------------------------------------------------

class TestHomeEndpoint:
    def test_home_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_status(self, client):
        response = client.get("/")
        body = response.json()
        assert "status" in body
