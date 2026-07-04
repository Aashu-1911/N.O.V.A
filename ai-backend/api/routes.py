from fastapi import APIRouter
from pydantic import BaseModel

from core.command_executor import (
    handle_chat_message,
    handle_voice_command,
    memory,
    voice_manager,
)
from core.command_executor_v2 import execute_command as execute_command_v2
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
    return handle_chat_message(request.message)


@router.post("/intent")
def detect_intent(request: ChatRequest):
    return parse_intent(request.message)


@router.post("/memory/clear")
def clear_memory():
    memory.clear()
    return {"status": "memory cleared"}


@router.get("/tasks")
def show_tasks():
    return get_tasks()


@router.get("/tasks/stats")
def task_stats():
    return get_task_stats()


@router.post("/execute")
def execute(request: TaskActionRequest):
    # Use the new command_executor_v2 which has app handlers implemented
    return execute_command_v2(request.message)


@router.delete("/tasks")
def remove_task(request: DeleteTaskRequest):
    success = delete_task(request.task_id)

    return {
        "success": success
    }


@router.post("/voice/start")
def voice_start():
    try:
        if not voice_manager.is_listening:
            voice_manager.start_listening()
        return {"status": "listening", "listening": voice_manager.is_listening}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/voice/stop")
def voice_stop():
    try:
        if voice_manager.is_listening:
            voice_manager.stop_listening()
        return {"status": "stopped", "listening": voice_manager.is_listening}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/voice/status")
def voice_status():
    return {"listening": voice_manager.is_listening}


@router.post("/voice/command")
def voice_command(request: ChatRequest):
    return handle_voice_command(request.message)