from fastapi import APIRouter
from pydantic import BaseModel

from core.command_executor import execute_command
from core.intent_parser import parse_intent
from managers.task_manager import delete_task, get_task_stats, get_tasks

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class DeleteTaskRequest(BaseModel):
    task_id: int


class TaskActionRequest(BaseModel):
    message: str
    task_id: int | None = None


@router.get("/")
def home():
    return {"status": "Jarvis Online"}


@router.post("/chat")
def chat(request: ChatRequest):
    """Backward-compatible chat endpoint — wraps execute_command."""
    return execute_command(request.message)


@router.post("/intent")
def detect_intent(request: ChatRequest):
    return parse_intent(request.message)


@router.get("/tasks")
def show_tasks():
    return get_tasks()


@router.get("/tasks/stats")
def task_stats():
    return get_task_stats()


@router.post("/execute")
def execute(request: TaskActionRequest):
    return execute_command(request.message)


@router.delete("/tasks")
def remove_task(request: DeleteTaskRequest):
    success = delete_task(request.task_id)
    return {"success": success}
