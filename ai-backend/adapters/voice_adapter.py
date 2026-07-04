"""
Voice Adapter — bridges Voice_Module callbacks to Command_Executor.

This is the ONLY module that imports both voice and command_executor.
It sits at the boundary between:
  - Voice_Module  (voice I/O, no business logic)
  - Command_Executor (business logic, no voice awareness)

Flow:
    VoiceInputManager  →  voice_command_callback()  →  execute_command()
                                                              ↓
                                speak(reply)  ←  response dict
"""
from __future__ import annotations

import logging
import re

from voice import speak
from core.command_executor_v2 import execute_command

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_for_voice(text: str) -> str:
    """
    Strip markdown and clean up text so it sounds natural when read aloud.

    Transformations applied:
    - Remove bold/italic markers  (**text**, *text*)
    - Remove inline code          (`code`)
    - Remove fenced code blocks   (```...```)
    - Convert markdown links      [label](url)  →  label
    - Remove heading markers      (# Heading)
    - Remove bullet/list markers  (- item, * item, 1. item)
    - Collapse extra whitespace
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
    """
    Handle a transcribed voice command.

    Registered with VoiceInputManager via::

        voice_manager.on_command(voice_command_callback)

    Args:
        command_text: Raw transcribed text from Voice_Module STT.
    """
    if not command_text or not command_text.strip():
        logger.debug("voice_command_callback received empty text, ignoring")
        return

    logger.info(f"[VoiceAdapter] Received command: {command_text!r}")

    try:
        # Delegate to the interface-agnostic Command_Executor
        response = execute_command(command_text)

        # Extract the user-facing reply
        reply = response.get("reply", "").strip()
        status = response.get("status", "success")

        if not reply:
            logger.warning("[VoiceAdapter] execute_command returned empty reply")
            speak("I processed your request but have nothing to say.")
            return

        # Apply voice-specific formatting (strip markdown, etc.)
        spoken_reply = format_for_voice(reply)

        if status == "error":
            logger.warning(f"[VoiceAdapter] Command returned error: {reply!r}")

        speak(spoken_reply)

    except Exception as exc:
        error_msg = "Sorry, something went wrong while processing your command."
        logger.exception(f"[VoiceAdapter] Unexpected error: {exc}")
        try:
            speak(error_msg)
        except Exception:
            # TTS itself failed — nothing more we can do here
            logger.exception("[VoiceAdapter] speak() also failed during error handling")
