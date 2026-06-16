import json
from ollama_client import send_message


SYSTEM_PROMPT = """
You are Jarvis's intent router.

Return ONLY valid JSON.

Supported intents:

add_task
complete_task
update_task
show_stats
open_website
open_application
general_chat

Examples:

User: Add a task to learn Docker tomorrow

{
  "intent": "add_task",
  "parameters": {
    "task_name": "learn Docker",
    "date": "tomorrow"
  }
}

User: Open YouTube

{
  "intent": "open_website",
  "parameters": {
    "website": "youtube"
  }
}
"""


def route_command(command: str):
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {command}"

    try:
        response = "".join(send_message(prompt, []))

        start = response.find("{")
        end = response.rfind("}") + 1

        response = "".join(send_message(prompt, []))

        print("\nRAW RESPONSE:")
        print(repr(response))
        print()
        
        return json.loads(response[start:end])

    except Exception as e:
        print("[ROUTER ERROR]", e)

        return {
            "intent": "general_chat",
            "parameters": {
                "message": command
            }
        }