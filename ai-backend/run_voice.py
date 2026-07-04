"""
run_voice.py — Start the NOVA voice assistant.

Usage:
    python run_voice.py

What it does:
    1. Loads the Whisper model (downloads on first run)
    2. Opens your microphone
    3. Listens continuously for commands
    4. Transcribes your speech and routes it through the command executor
    5. Speaks the response back via TTS

Say any of these to test:
    "Add task to learn Docker"
    "Show my tasks"
    "Open browser"
    "Search Google for weather"
    "Open Notepad"
    "Take screenshot"
    "Mute"
    "What time is it"
"""

import sys
import os

# Ensure ai-backend root is on the path when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VOICE_MODEL
from database import init_db
from managers.app_manager import load_start_menu_apps
from voice.stt import VoiceInputManager
from adapters.voice_adapter import voice_command_callback
from voice.tts import _default_tts_manager


def main():
    print("=" * 50)
    print("  NOVA Voice Assistant")
    print("=" * 50)

    # Initialize database and app cache
    print("[INIT] Setting up database...")
    init_db()

    print("[INIT] Loading installed apps...")
    load_start_menu_apps()

    # Pre-warm TTS worker thread so COM/pyttsx3 init happens now,
    # not mid-command where it blocks the voice callback thread.
    print("[INIT] Warming up TTS engine...")
    _default_tts_manager._ensure_worker()
    print("[INIT] TTS ready.")

    # Register voice callback and start listening
    # Whisper model loads in the background thread when start_listening() is called
    print(f"[INIT] Starting voice listener with Whisper '{VOICE_MODEL}' model...")
    print("[INFO]  Whisper will load in the background — this takes 1-3 min on first run.")
    vm = VoiceInputManager(model_name=VOICE_MODEL)
    vm.on_command(voice_command_callback)

    print("\n[READY] Mic is open. Speak a command after the model loads...")
    print("[INFO]  You will see '[VOICE] Waiting for speech...' when ready.")
    print("[INFO]  Press Ctrl+C to stop.\n")

    vm.start_listening(background=False)  # blocks here, runs the loop


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] NOVA shutting down.")
