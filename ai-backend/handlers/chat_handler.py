"""
Chat handler - handles general_chat and answer_question intents using the LLM.
"""

from typing import Dict, Optional

from core.response_builder import success, error
from services.ollama_service import send_message as ollama_send_message, OllamaConnectionError


def handle_general_chat(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for general chat and fallback for unknown intents using LLM."""
    raw_command = context.get("raw_command", "") if context else ""

    if not raw_command:
        return error("I didn't receive any input to process.")

    try:
        # Collect streaming response from Ollama LLM
        chunks = list(ollama_send_message(raw_command))
        reply = "".join(chunks).strip()

        if not reply:
            return error("I received an empty response. Please try again.")

        return success(reply)

    except OllamaConnectionError:
        return error("I'm unable to connect to the AI service right now. Please make sure Ollama is running.")
    except Exception as e:
        return error(
            "I encountered an error processing your request. Please try again.",
            payload={"error": str(e)},
        )
