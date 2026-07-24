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
import threading
import time

# Ensure ai-backend root is on the path when running from any directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VOICE_MODEL
from database import init_db
from managers.app_manager import load_start_menu_apps
from voice.stt import VoiceInputManager, KeyboardHookListener
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

    # Load VoiceInputManager and pre-load Whisper
    from core.context_manager import ExecutionContextManager
    context_manager = ExecutionContextManager()

    print(f"[INIT] Starting voice listener with Whisper '{VOICE_MODEL}' model...")
    vm = VoiceInputManager(model_name=VOICE_MODEL)
    vm.on_command(lambda text: voice_command_callback(text, context_manager=context_manager))
    
    print("[INIT] Pre-loading Whisper model (this takes 1-3 min on first run)...")
    vm._load_model()
    print("[INIT] Whisper model loaded successfully.")

    # Callbacks for Keyboard Listener
    def on_press():
        if vm.state != vm.STATE_IDLE:
            return
        vm.start_recording()

    def on_release():
        audio_path = vm.stop_recording()
        
        def process_and_execute():
            vm.set_state(vm.STATE_PROCESSING)
            req_id = f"ptt_{vm._request_counter:02d}"
            cmd_text = vm.transcribe_audio(audio_path, req_id=req_id)
            
            # Clean up the file after transcription
            try:
                from pathlib import Path
                Path(audio_path).unlink(missing_ok=True)
            except Exception:
                pass

            if cmd_text:
                vm.set_state(vm.STATE_SPEAKING)
                voice_command_callback(cmd_text, context_manager=context_manager)
            
            vm.set_state(vm.STATE_IDLE)

        threading.Thread(target=process_and_execute, daemon=True).start()

    # Start keyboard hook listener
    listener = KeyboardHookListener(on_press=on_press, on_release=on_release)
    listener.start()

    print("\n[READY] Push-to-Talk is ready!")
    print("[INFO]  HOLD Ctrl + Space to speak, and RELEASE to execute.")
    print("[INFO]  Press Ctrl+C to exit.\n")
    
    # Set initial state
    vm.set_state(vm.STATE_IDLE)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
    finally:
        listener.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] NOVA shutting down.")
