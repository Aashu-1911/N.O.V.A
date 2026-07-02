from __future__ import annotations

from typing import Dict, Optional

from config import VOICE_MODEL
from core.conversation import ConversationManager
from core.intent_parser import parse_intent
from core.intent_router import route_command
from managers.app_manager import close_application, open_application
from managers.browser_manager import open_website
from managers.media_manager import play_media
from managers.system_manager import (
    lock_pc,
    mute_volume,
    take_screenshot,
    unmute_volume,
    volume_down,
    volume_up,
)
from managers.task_manager import (
    add_task,
    complete_task,
    get_task_stats,
    update_task,
)
from services.llm_service import send_message
from voice import VoiceInputManager, speak


memory = ConversationManager()
voice_manager = VoiceInputManager(model_name=VOICE_MODEL)


def _normalize_command(command: str) -> str:
    parts = [part.strip() for part in command.split(".") if part.strip()]
    if len(parts) >= 2 and parts[0] == parts[1]:
        return parts[0]
    return command


def _resolve_intent(command: str) -> Dict[str, object]:
    result = parse_intent(command)

    if result["confidence"] >= 0.8:
        return result

    llm_result = route_command(command)

    candidate = llm_result.get("parameters", {}).get("url", "").lower()

    if llm_result["intent"] == "open_website" and command.lower().startswith("open "):
        candidate = llm_result.get("parameters", {}).get("url")
        if candidate and "." not in candidate:
            llm_result = {
                "intent": "open_application",
                "parameters": {
                    "app_name": candidate,
                },
            }

    entities = llm_result.get("parameters", {})

    return {
        "intent": llm_result["intent"],
        "entities": entities,
        "confidence": 1.0,
    }


def handle_chat_message(message: str) -> Dict[str, str]:
    memory.add_message("user", message)

    response = "".join(send_message(message, memory.get_history()))

    memory.add_message("assistant", response)
    return {
        "user_message": message,
        "response": response,
    }


def execute_command(message: str, task_id: Optional[int] = None) -> Dict[str, object]:
    result = _resolve_intent(message)
    intent = result["intent"]
    entities = result["entities"]
    task_identifier = task_id or entities.get("task_name")

    if intent == "add_task":
        if not entities.get("task_name"):
            return {
                "status": "error",
                "intent": intent,
                "reply": "I understood you want to add a task, but I could not determine the task name.",
            }

        task = add_task(
            entities.get("task_name"),
            entities.get("date"),
            entities.get("category"),
            entities.get("priority"),
        )
        return {
            "status": "success",
            "intent": intent,
            "task": task,
        }

    if intent == "complete_task":
        task = complete_task(task_identifier)
        return {
            "status": "success" if task else "not_found",
            "intent": intent,
            "task": task,
        }

    if intent == "update_task" and task_identifier is not None:
        task = update_task(
            task_identifier,
            task_name=entities.get("task_name"),
            date=entities.get("date"),
            category=entities.get("category"),
            priority=entities.get("priority"),
        )
        return {
            "status": "success" if task else "not_found",
            "intent": intent,
            "task": task,
        }

    if intent == "show_stats":
        return {
            "status": "success",
            "intent": intent,
            "stats": get_task_stats(),
        }

    if intent == "open_website":
        return {
            "status": "handled",
            "intent": intent,
            "entities": entities,
        }

    if intent == "reminder":
        return {
            "status": "handled",
            "intent": intent,
            "entities": entities,
        }

    return {
        "status": "ignored",
        "intent": intent,
        "entities": entities,
    }


def handle_voice_command(command: str) -> Dict[str, object]:
    command = _normalize_command(command)

    memory.add_message("user", command)

    result = _resolve_intent(command)
    intent = result["intent"]
    entities = result["entities"]

    if intent == "add_task":
        if not entities.get("task_name"):
            reply = (
                f"I heard: {command}. "
                "I understood you want to add a task, but I could not determine the task name."
            )
            memory.add_message("assistant", reply)
            speak(reply)
            return {
                "status": "error",
                "intent": intent,
                "reply": reply,
            }

        task = add_task(
            entities.get("task_name"),
            entities.get("date"),
            entities.get("category"),
            entities.get("priority"),
        )
        reply = f"Added task: {task['task_name']}"
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success",
            "intent": intent,
            "reply": reply,
        }

    if intent == "complete_task":
        task_identifier = entities.get("task_name")
        task = complete_task(task_identifier)
        reply = f"Marked '{task['task_name']}' complete." if task else "Task not found."
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success" if task else "not_found",
            "intent": intent,
            "reply": reply,
        }

    if intent == "update_task":
        task_identifier = entities.get("task_name")
        task = update_task(
            task_identifier,
            task_name=entities.get("task_name"),
            date=entities.get("date"),
            category=entities.get("category"),
            priority=entities.get("priority"),
        )
        reply = "Updated task." if task else "Task not found."
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success" if task else "not_found",
            "intent": intent,
            "reply": reply,
        }

    if intent == "show_stats":
        stats = get_task_stats()
        reply = f"You have {stats['pending']} pending and {stats['completed']} completed tasks."
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success",
            "intent": intent,
            "reply": reply,
            "stats": stats,
        }

    if intent == "reminder":
        task_name = entities.get("task_name")
        if not task_name:
            reply = "I could not understand the reminder."
            memory.add_message("assistant", reply)
            speak(reply)
            return {
                "status": "error",
                "intent": intent,
                "reply": reply,
            }

        task = add_task(
            task_name,
            entities.get("date"),
            "reminder",
            "medium",
        )
        reply = f"Reminder created for {task['task_name']}"
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success",
            "intent": intent,
            "reply": reply,
            "task": task,
        }

    if intent == "open_website":
        website = entities.get("url")
        success = open_website(website)
        reply = f"Opening {website.replace('https://', '').replace('http://', '')}" if success else "I could not find that website."
        speak(reply)
        return {
            "status": "success" if success else "error",
            "reply": reply,
        }

    if intent == "open_application":
        app_name = entities.get("app_name") or entities.get("application")
        success = open_application(app_name)
        reply = f"Opening {app_name}" if success else f"I could not find {app_name}"
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success" if success else "error",
            "intent": intent,
            "reply": reply,
        }

    if intent == "take_screenshot":
        take_screenshot()
        reply = "Screenshot saved in your Screenshots folder."
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success",
            "reply": reply,
        }

    if intent == "lock_pc":
        lock_pc()
        return {
            "status": "success",
        }

    if intent == "volume_control":
        action = entities.get("volume_action")
        if action == "mute":
            mute_volume()
        elif action == "unmute":
            unmute_volume()
        elif action == "up":
            volume_up()
        elif action == "down":
            volume_down()
        return {
            "status": "success",
            "intent": intent,
        }

    if intent == "media_control":
        action = entities.get("media_action")
        query = entities.get("media_query")
        if action == "play" and query:
            success = play_media(query)
            reply = f"Playing {query}"
            memory.add_message("assistant", reply)
            speak(reply)
            return {
                "status": "success" if success else "error",
                "intent": intent,
                "reply": reply,
            }

    if intent == "close_application":
        app_name = entities.get("app_name")
        success = close_application(app_name)
        reply = f"Closed {app_name}" if success else f"Could not close {app_name}"
        memory.add_message("assistant", reply)
        speak(reply)
        return {
            "status": "success" if success else "error",
            "reply": reply,
            "intent": intent,
        }

    try:
        llm_reply = "".join(send_message(command, memory.get_history()))
    except Exception:
        llm_reply = "Sorry, I couldn't process that right now."

    memory.add_message("assistant", llm_reply)
    speak(llm_reply)
    return {
        "status": "replied",
        "intent": intent,
        "reply": llm_reply,
    }


voice_manager.on_command(handle_voice_command)
