Voice / STT for Jarvis (Phase 2)
================================

This folder contains the speech-to-text helpers used by Jarvis.

Quick start (requires a Python virtualenv with dependencies):

1. Install dependencies from `requirements.txt` in `ai-backend`.

2. Example usage:

```py
from voice import VoiceInputManager

mgr = VoiceInputManager(model_name="small")

def handle(cmd: str):
    print("Command:", cmd)

mgr.on_command(handle)
mgr.start_listening()

# ... later
mgr.stop_listening()
```

Notes:
- Model loading may take time the first time you call `start_listening()`.
- Running everything locally requires `openai-whisper` and an audio backend.
