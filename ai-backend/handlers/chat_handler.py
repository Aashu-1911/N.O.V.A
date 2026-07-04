"""
Chat handler - handles general_chat and answer_question intents using the LLM.
"""

from typing import Dict, Optional

from services.ollama_service import send_message as ollama_send_message, OllamaConnectionError


def handle_general_chat(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for general chat and fallback for unknown intents using LLM."""
    raw_command = context.get("raw_command", "") if context else ""

    if not raw_command:
        return {
            "status": "error",
            "reply": "I didn't receive any input to process.",
            "payload": {}
        }

    try:
        # Collect streaming response from Ollama LLM
        chunks = list(ollama_send_message(raw_command))
        reply = "".join(chunks).strip()

        if not reply:
            return {
                "status": "error",
                "reply": "I received an empty response. Please try again.",
                "payload": {}
            }

        return {
            "status": "success",
            "reply": reply,
            "payload": {}
        }

    except OllamaConnectionError:
        return {
            "status": "error",
            "reply": "I'm unable to connect to the AI service right now. Please make sure Ollama is running.",
            "payload": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "reply": "I encountered an error processing your request. Please try again.",
            "payload": {"error": str(e)}
        }
