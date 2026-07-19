"""
Chat handler - handles general_chat and answer_question intents using the LLM.

All functions accept an ``entities`` dict (extracted by the intent parser) and an
optional ``context`` dict.  They return a ``ResponseDict`` built with
:mod:`core.response_builder` helpers.

This module has NO voice imports and NO HTTP framework imports.
"""

from typing import Any, Dict, Optional

from core.response_builder import success, error
from services.ollama_service import send_message as ollama_send_message, OllamaConnectionError

# Convenience alias for the structured response dict returned by every handler.
ResponseDict = Dict[str, Any]


def handle_general_chat(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle general-chat and fallback intents by forwarding to the local LLM.

    This handler is also used as the **fallback** for any intent that does not
    have a dedicated handler in the HANDLERS dict.  It reads the original user
    message from ``context["raw_command"]`` and streams a response from the
    Ollama service.

    Args:
        entities: Intent entities (not used; the raw command is read from
            ``context`` instead).
        context: Optional session / request context.  Expected keys:

            - ``raw_command`` *(str, required)* — the original user input
              forwarded by :func:`core.command_executor.execute_command`.

    Returns:
        ResponseDict with ``status="success"`` and the LLM reply in ``reply``,
        or ``status="error"`` if the Ollama service is unreachable, the reply is
        empty, or an unexpected exception occurs.

    Raises:
        No exceptions are raised; all errors are returned as ``status="error"``
        response dicts.

    Example::

        result = handle_general_chat(
            {},
            context={"raw_command": "What time is it in Tokyo?"},
        )
        # {"status": "success", "reply": "It is currently …"}
    """
    raw_command = context.get("raw_command", "") if context else ""

    if not raw_command:
        return error("I didn't receive any input to process.")

    try:
        # Collect response chunks from Ollama LLM
        # send_message now returns a List[str] with the connection properly closed
        chunks = ollama_send_message(raw_command)
        reply = "".join(chunks).strip()

        if not reply:
            return error("I received an empty response. Please try again.")

        return success(reply)

    except OllamaConnectionError:
        return error(
            "I'm having trouble reaching my language model right now. "
            "You can still ask me to open applications, browse the web, or control your computer."
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(
            "I'm having trouble reaching my language model right now. "
            "You can still ask me to open applications, browse the web, or control your computer.",
            payload={"error": str(e)},
        )
