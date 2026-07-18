"""
Voice Adapter — bridges Voice_Module callbacks to Command_Executor.

This is the **ONLY** module that imports from both ``voice/`` and
``core/command_executor``.  It sits at the boundary between:

- **Voice_Module** (``voice/``) — handles audio I/O, knows nothing about
  business logic, managers, or command routing.
- **Command_Executor** (``core/command_executor``) — handles intent routing and
  business logic, knows nothing about voice, audio, or TTS.

Architecture position::

    VoiceInputManager  →  voice_command_callback()  →  execute_command()
                                                               ↓
                               speak(reply)  ←  ResponseDict

Usage — register the callback at application startup::

    from voice import VoiceInputManager
    from adapters.voice_adapter import voice_command_callback

    voice_manager = VoiceInputManager(model_name="small")
    voice_manager.on_command(voice_command_callback)
    voice_manager.start_listening()

Dependency rule
---------------
``voice/``  **MUST NOT** import from ``core/``, ``handlers/``, or ``managers/``.
``core/command_executor``  **MUST NOT** import from ``voice/``.
This adapter is the **sole integration point** and the only file allowed to
cross that boundary.
"""
from __future__ import annotations

import logging
import re

from voice import speak
from core.command_executor import execute_command

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_for_voice(text: str) -> str:
    """Strip markdown and clean up text so it sounds natural when read aloud.

    Transformations applied (in order):

    1. Remove fenced code blocks (``\\`\\`\\`...\\`\\`\\``).
    2. Remove inline code backticks but keep the content.
    3. Remove bold (``**`` / ``__``) and italic (``*`` / ``_``) markers.
    4. Convert markdown links ``[label](url)`` → ``label``.
    5. Remove heading markers (``#``, ``##``, …).
    6. Remove list markers (``-``, ``*``, ``1.``, ``2.``, …).
    7. Collapse multiple whitespace / newlines to a single space.

    Args:
        text: Raw reply text that may contain markdown formatting.

    Returns:
        Plain-text string suitable for TTS synthesis.

    Example::

        result = format_for_voice("**Added task:** `learn Docker`")
        # "Added task: learn Docker"

        result = format_for_voice("Here are your tasks:\\n- Task A\\n- Task B")
        # "Here are your tasks: Task A Task B"
    """
    # Remove fenced code blocks entirely
    formatted = re.sub(r"```[\s\S]*?```", "", text)

    # Remove inline code backticks but keep the content
    formatted = re.sub(r"`([^`]*)`", r"\1", formatted)

    # Remove bold / italic markers
    formatted = formatted.replace("**", "").replace("__", "")
    formatted = re.sub(r"(?<!\*)\*(?!\*)", "", formatted)  # single *
    formatted = re.sub(r"(?<!_)_(?!_)", "", formatted)      # single _

    # Convert markdown links to just the label
    formatted = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", formatted)

    # Remove heading markers
    formatted = re.sub(r"^#{1,6}\s+", "", formatted, flags=re.MULTILINE)

    # Remove list markers (-, *, 1., 2., …)
    formatted = re.sub(r"^\s*[-*]\s+", "", formatted, flags=re.MULTILINE)
    formatted = re.sub(r"^\s*\d+\.\s+", "", formatted, flags=re.MULTILINE)

    # Collapse whitespace / newlines to single spaces
    formatted = re.sub(r"\s+", " ", formatted).strip()

    return formatted


# ---------------------------------------------------------------------------
# Callback registered with VoiceInputManager
# ---------------------------------------------------------------------------

def voice_command_callback(command_text: str) -> None:
    """Handle a transcribed voice command end-to-end.

    This function is designed to be registered with
    :class:`voice.VoiceInputManager` via :meth:`~voice.VoiceInputManager.on_command`::

        voice_manager.on_command(voice_command_callback)

    When a voice command is transcribed, the flow is:

    1. Validate that ``command_text`` is non-empty.
    2. Call :func:`core.command_executor.execute_command` with the raw text.
    3. Extract the ``"reply"`` value from the response dict.
    4. Apply :func:`format_for_voice` to strip markdown.
    5. Call :func:`voice.speak` with the cleaned reply.
    6. On any exception, call :func:`voice.speak` with a fallback error message.

    Args:
        command_text: Raw transcribed text received from the STT engine
            (e.g. ``"Add task to learn Docker"``).

    Returns:
        ``None``.  Side-effects only: calls ``speak()`` with the assistant reply.

    Raises:
        No exceptions are propagated.  All errors are caught and spoken aloud
        so the user receives audio feedback even when something goes wrong.

    Example::

        # Registered automatically via on_command(); not normally called directly.
        voice_command_callback("Show my tasks")
        # → calls speak("Here are your tasks: …")
    """
    if not command_text or not command_text.strip():
        logger.debug("voice_command_callback received empty text, ignoring")
        return

    logger.info(f"[VoiceAdapter] Received command: {command_text!r}")

    try:
        from core.intent_parser import parse_intent
        from core.command_executor import HANDLERS

        print("[INSTRUMENTATION] execute_command entered")
        
        # Log parsed intent, entities, and selected handler
        try:
            parsed = parse_intent(command_text)
            intent = parsed.get("intent")
            entities = parsed.get("entities")
            handler = HANDLERS.get(intent, HANDLERS.get("answer_question"))
            print(f"[INSTRUMENTATION] intent: {intent}")
            print(f"[INSTRUMENTATION] entities: {entities}")
            print(f"[INSTRUMENTATION] handler selected: {handler.__name__ if handler else 'None'}")
        except Exception as e:
            print(f"[INSTRUMENTATION] Failed to parse intent/handler for logging: {e}")

        # Delegate to the interface-agnostic Command_Executor
        response = execute_command(command_text)
        print("[INSTRUMENTATION] execute_command exited")
        print("[INSTRUMENTATION] handler exited")
        print(f"[INSTRUMENTATION] ResponseDict: {response}")

        # Extract the user-facing reply
        reply = response.get("reply", "").strip()
        status = response.get("status", "success")
        print(f"[INSTRUMENTATION] reply: {reply!r}")

        if not reply:
            logger.warning("[VoiceAdapter] execute_command returned empty reply")
            print("[INSTRUMENTATION] TTS called (empty reply fallback)")
            speak("I processed your request but have nothing to say.")
            print("[INSTRUMENTATION] TTS finished")
            return

        # Apply voice-specific formatting (strip markdown, etc.)
        spoken_reply = format_for_voice(reply)

        if status == "error":
            logger.warning(f"[VoiceAdapter] Command returned error: {reply!r}")

        print("[INSTRUMENTATION] TTS called")
        speak(spoken_reply)
        print("[INSTRUMENTATION] TTS finished")

    except Exception as exc:
        error_msg = "Sorry, something went wrong while processing your command."
        logger.exception(f"[VoiceAdapter] Unexpected error: {exc}")
        try:
            print("[INSTRUMENTATION] TTS called (error fallback)")
            speak(error_msg)
            print("[INSTRUMENTATION] TTS finished (error fallback)")
        except Exception:
            # TTS itself failed — nothing more we can do here
            logger.exception("[VoiceAdapter] speak() also failed during error handling")
