import json
import requests

ROUTER_MODEL = "qwen2.5:1.5b"

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
reminder
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

User: Open YouTube

{
  "intent": "open_website",
  "parameters": {
    "url": "youtube"
  }
}

User: Remind me to call mom tomorrow

{
  "intent": "reminder",
  "parameters": {
    "task_name": "call mom",
    "date": "tomorrow"
  }
}

Always include:
- intent
- parameters

Return JSON only.
"""


def route_command(command: str):

    prompt = f"{SYSTEM_PROMPT}\n\nUser: {command}"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": ROUTER_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        raw_response = data.get("response", "").strip()

        print("\n[ROUTER RAW]")
        print(raw_response)

        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1

        if start == -1 or end <= 0:
            raise ValueError("No JSON found")

        json_text = raw_response[start:end]

        return json.loads(json_text)

    except Exception as e:
        print("[ROUTER ERROR]", e)

        return {
            "intent": "general_chat",
            "parameters": {
                "message": command
            }
        }