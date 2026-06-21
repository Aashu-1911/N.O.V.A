from fastapi import FastAPI
from pydantic import BaseModel
from conversation import ConversationManager
from ollama_client import send_message, parse_intent
from intent_router import route_command
from voice import speak
from media_manager import play_media
# from system_manager import lock_pc, take_screenshot
from app_manager import (
    open_application,
    close_application,
)
from app_manager import load_start_menu_apps

from system_manager import (
    lock_pc,
    take_screenshot,
    mute_volume,
    unmute_volume,
    volume_up,
    volume_down,
)

from app_manager import open_application
from browser_manager import open_website
from task_manager import (
    add_task,
    complete_task,
    delete_task,
    get_task_stats,
    get_tasks,
    update_task,
)
from database import init_db
from voice import VoiceInputManager
import os

app = FastAPI(title="Jarvis AI")
init_db()


class ChatRequest(BaseModel):
    message: str

class DeleteTaskRequest(BaseModel):
    task_id: int


class TaskActionRequest(BaseModel):
    message: str
    task_id: int | None = None
    
    
@app.get("/")
def home():
    return {"status": "Jarvis Online"}


@app.post("/chat")
def chat(request: ChatRequest):
    memory.add_message("user", request.message)

    response = "".join(
        send_message(
            request.message,
            memory.get_history()
        )
    )

    memory.add_message("assistant", response)

    return {
        "user_message": request.message,
        "response": response
    }
    

@app.post("/intent")
def detect_intent(request: ChatRequest):
    return parse_intent(request.message)

memory = ConversationManager()

# Voice manager (lazy model load inside the class)
VOICE_MODEL = os.getenv("VOICE_MODEL", "medium")
voice_manager = VoiceInputManager(model_name=VOICE_MODEL)
voice_manager.on_command(lambda text: _handle_voice_command(text))

def needs_correction(intent, entities):
    if intent == "add_task" and not entities.get("task_name"):
        return True

    if intent == "open_website" and not entities.get("url"):
        return True

    return False

def _handle_voice_command(command: str) -> dict:
    """Process a transcribed voice command similarly to the /execute route.

    Returns a small dict with status and optional reply text.
    """
    
    parts = [p.strip() for p in command.split(".") if p.strip()]
    if len(parts) >= 2 and parts[0] == parts[1]:
        command = parts[0]
    
       
    print(f"[VOICE] Processing command: {command}")
    memory.add_message("user", command)

    result = parse_intent(command)
    
    print(f"[PARSER] Confidence: {result['confidence']}")
    if result["confidence"] < 0.8:
        print("[ROUTER] Falling back to qwen2.5 router")
        
        llm_result = route_command(command)
        
        KNOWN_WEBSITES = {
            "youtube",
            "github",
            "google",
            "linkedin",
            "stackoverflow",
            "chatgpt"
        }

        candidate = (
            llm_result.get("parameters", {})
            .get("url", "")
            .lower()
        )
        
        if (
            llm_result["intent"] == "open_website"
            and command.lower().startswith("open ")
        ):
            candidate = llm_result.get("parameters", {}).get("url")

            if candidate and "." not in candidate:
                llm_result = {
                    "intent": "open_application",
                    "parameters": {
                        "app_name": candidate
                    }
                }
        
        entities = llm_result.get("parameters", {})

        

        result = {
            "intent": llm_result["intent"],
            "entities": entities,
            "confidence": 1.0
        }
    print(f"[VOICE] Intent result: {result}")
        
    intent = result["intent"]
    entities = result["entities"]
    print(f"[VOICE] Intent variable = {intent}")
    
    if intent == "add_task":
        print(f"[VOICE] Adding task: {entities}")
        if not entities.get("task_name"):
            reply = (
                f"I heard: {command}. "
                "I understood you want to add a task, "
                "but I could not determine the task name."
            )
           
            memory.add_message("assistant", reply)
            speak(reply)
            return {
                "status": "error",
                "intent": intent,
                "reply": reply
            }
        task = add_task(
            entities.get("task_name"),
            entities.get("date"),
            entities.get("category"),
            entities.get("priority"),
        )
        reply = f"Added task: {task['task_name']}"
        memory.add_message("assistant", reply)
        print(f"[TTS] Speaking: {reply}")
        speak(reply)
        return {"status": "success", "intent": intent, "reply": reply}

    if intent == "complete_task":
        task_identifier = entities.get("task_name")
        task = complete_task(task_identifier)
        if task:
            reply = f"Marked '{task['task_name']}' complete."
        else:
            reply = "Task not found."
        memory.add_message("assistant", reply)
        speak(reply)
        return {"status": "success" if task else "not_found", "intent": intent, "reply": reply}

    if intent == "update_task":
        task_identifier = entities.get("task_name")
        task = update_task(
            task_identifier,
            task_name=entities.get("task_name"),
            date=entities.get("date"),
            category=entities.get("category"),
            priority=entities.get("priority"),
        )
        reply = f"Updated task." if task else "Task not found."
        memory.add_message("assistant", reply)
        speak(reply)
        return {"status": "success" if task else "not_found", "intent": intent, "reply": reply}

    if intent == "show_stats":
        stats = get_task_stats()
        reply = f"You have {stats['pending']} pending and {stats['completed']} completed tasks."
        memory.add_message("assistant", reply)
        speak(reply)
        return {"status": "success", "intent": intent, "reply": reply, "stats": stats}

    if intent == "reminder":
        print("[REMINDER] Entered reminder block")
        task_name = entities.get("task_name")

        if not task_name:
            reply = "I could not understand the reminder."

            memory.add_message("assistant", reply)
            speak(reply)

            return {
                "status": "error",
                "intent": intent,
                "reply": reply
            }

        task = add_task(
            task_name,
            entities.get("date"),
            "reminder",
            "medium"
        )

        reply = f"Reminder created for {task['task_name']}"

        memory.add_message("assistant", reply)
        speak(reply)

        return {
            "status": "success",
            "intent": intent,
            "reply": reply,
            "task": task
        }

    if intent == "open_website":
        print("[BROWSER] Entered open_website block")
        website = entities.get("url")
        print(f"[BROWSER] Website: {website}")
        success = open_website(website)
        print(f"[BROWSER] Success: {success}")
        if success:
            website_name = website.replace("https://", "").replace("http://", "")
            reply = f"Opening {website_name}"
        else:
            reply = "I could not find that website."
        print(f"[BROWSER] Reply: {reply}")
        speak(reply)
        return {
            "status": "success",
            "reply": reply
        }
        
    
    #open application
    if intent == "open_application":

        app_name = (
            entities.get("app_name")
            or entities.get("application")
        )

        print(f"[APP] Opening: {app_name}")

        success = open_application(app_name)

        if success:
            reply = f"Opening {app_name}"
        else:
            reply = f"I could not find {app_name}"

        memory.add_message("assistant", reply)
        speak(reply)

        return {
            "status": "success" if success else "error",
            "intent": intent,
            "reply": reply
        }
    
    #take screenshot
    if intent == "take_screenshot":

        path = take_screenshot()

        reply = "Screenshot saved in your Screenshots folder."

        memory.add_message("assistant", reply)
        speak(reply)

        return {
            "status": "success",
            "reply": reply
        }
    
    # lock pc
    # if intent == "lock_pc":

    #     print("[SYSTEM] Lock PC intent triggered")

    #     reply = "Locking computer."

    #     memory.add_message("assistant", reply)
    #     speak(reply)
    #     print("[SYSTEM] About to call lock_pc()")

    #     lock_pc()
    #     print("[SYSTEM] lock_pc() finished")
    #     return {
    #         "status": "success",
    #         "reply": reply
    #     }
    if intent == "lock_pc":
        print("[SYSTEM] Lock PC intent triggered")

        lock_pc()

        return {
            "status": "success"
        }
    
    
    #volutme control
    if intent == "volume_control":

        action = entities.get("volume_action")

        print(f"[VOLUME] Action: {action}")

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
            "intent": intent
        }
        
    
    # Media intent execution
    if intent == "media_control":
        action = entities.get("media_action")
        query = entities.get("media_query")
        print(f"[MEDIA] Action: {action}")
        print(f"[MEDIA] Query: {query}")
        if action == "play" and query:
            success = play_media(query)
            reply = f"Playing {query}"
            memory.add_message("assistant", reply)
            speak(reply)
            
            return {
                "status": "success" if success else "error",
                "intent": intent,
                "reply": reply
            }
    
    
    #close application
    if intent == "close_application":
        app_name = entities.get("app_name")
        print(f"[APP] Closing: {app_name}")
        success = close_application(app_name)
        reply = (
            f"Closed {app_name}"
            if success
            else f"Could not close {app_name}"
        )

        memory.add_message("assistant", reply)
        speak(reply)

        return {
            "status": "success" if success else "error",
            "reply": reply,
            "intent": intent,
        }
    
    # Fallback: ask the LLM for a reply and store it
    try:
        llm_reply = "".join(send_message(command, memory.get_history()))
    except Exception:
        llm_reply = "Sorry, I couldn't process that right now."

    memory.add_message("assistant", llm_reply)
    speak(llm_reply)
    return {"status": "replied", "intent": intent, "reply": llm_reply}

@app.post("/memory/clear")
def clear_memory():
    memory.clear()
    return {"status": "memory cleared"}

@app.get("/tasks")
def show_tasks():
    return get_tasks()


@app.get("/tasks/stats")
def task_stats():
    return get_task_stats()

@app.post("/execute")
def execute(request: TaskActionRequest):

    result = parse_intent(request.message)

    intent = result["intent"]
    entities = result["entities"]
    task_identifier = request.task_id or entities.get("task_name")

    if intent == "add_task":
        task = add_task(
            entities["task_name"],
            entities.get("date"),
            entities.get("category"),
            entities.get("priority"),
        )

        return {
            "status": "success",
            "intent": intent,
            "task": task
        }

    elif intent == "complete_task":
        task = complete_task(task_identifier)

        return {
            "status": "success" if task else "not_found",
            "intent": intent,
            "task": task
        }

    elif intent == "update_task" and task_identifier is not None:
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

    elif intent == "show_stats":
        return {
            "status": "success",
            "intent": intent,
            "stats": get_task_stats(),
        }

    elif intent == "open_website":
        return {
            "status": "handled",
            "intent": intent,
            "entities": entities,
        }

    elif intent == "reminder":
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
    

@app.delete("/tasks")
def remove_task(request: DeleteTaskRequest):

    success = delete_task(request.task_id)

    return {
        "success": success
    }


@app.post("/voice/start")
def voice_start():
    try:
        if not voice_manager.is_listening:
            voice_manager.start_listening()
        return {"status": "listening", "listening": voice_manager.is_listening}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@app.post("/voice/stop")
def voice_stop():
    try:
        if voice_manager.is_listening:
            voice_manager.stop_listening()
        return {"status": "stopped", "listening": voice_manager.is_listening}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@app.get("/voice/status")
def voice_status():
    return {"listening": voice_manager.is_listening}


@app.post("/voice/command")
def voice_command(request: ChatRequest):
    result = _handle_voice_command(request.message)
    return result

@app.on_event("startup")
def startup_event():
    load_start_menu_apps()
    print("Application started")
