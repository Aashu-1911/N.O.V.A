from ollama_client import send_message

def cleanup_task_command(command: str) -> str:
    prompt = f"""
You are fixing a speech-to-text transcript.

The transcript is intended to be a task command.

Rules:
- Correct speech recognition mistakes.
- Preserve the user's meaning.
- Return only the corrected command.
- Do not explain anything.

Transcript:
{command}
"""

    try:
        return "".join(send_message(prompt, [])).strip()
    except Exception:
        return command