# Voice Module

The `voice/` module handles **all audio I/O for the assistant** — microphone capture,
speech-to-text (STT), text-to-speech (TTS), and wake-word detection. It knows nothing
about command execution, intent parsing, task managers, or any other business logic.
The module is intentionally interface-agnostic: it receives text from the outside world
and delivers text back. What happens to that text is the concern of the caller.

---

## Three-Layer Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        INPUT ADAPTERS                               │
│                                                                     │
│   Microphone / Audio ──► VoiceInputManager (voice/stt.py)         │
│                                 │                                   │
│                          callback(text)                             │
│                                 │                                   │
│                                 ▼                                   │
│        adapters/voice_adapter.py  ◄── ONLY file importing          │
│             (voice_command_callback)       both voice + executor    │
└─────────────────────────┬───────────────────────────────────────────┘
                           │  execute_command(text)
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                   CORE LAYER  (Interface-Agnostic)                  │
│                                                                     │
│           core/command_executor.py                                  │
│           execute_command(text) → ResponseDict                      │
│               │                                                     │
│               └─► handlers/* ──► managers/* / services/*           │
└─────────────────────────┬───────────────────────────────────────────┘
                           │  {"status", "reply", "payload", "intent"}
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                       OUTPUT ADAPTERS                               │
│                                                                     │
│   Voice path: voice_adapter.py ──► speak(reply)  (voice/tts.py)   │
│   API path:   api/routes.py    ──► return JSON                     │
│   Future:     gui_adapter.py   ──► display in UI                   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Module File Structure

```
voice/
├── __init__.py      Public API re-exports (speak, VoiceInputManager, …)
├── stt.py           VoiceInputManager — audio capture & Whisper transcription
├── tts.py           TTSManager — pyttsx3 / Coqui TTS synthesis & playback
└── wake_word.py     contains_wake_word() — simple substring wake-word check
```

---

## Public API

All symbols below are accessible directly from the `voice` package:

```python
from voice import (
    VoiceInputManager,
    TTSManager,
    speak,
    speak_async,
    synthesize,
    contains_wake_word,
)
```

### `VoiceInputManager`

Manages the microphone, Whisper transcription, and command callbacks.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(model_name="small", samplerate=16000, channels=1, wake_words=None)` | Create manager. `model_name` selects the Whisper model. |
| `start_listening` | `(background=True) → None` | Begin continuous audio capture loop. Runs in a daemon thread by default. |
| `stop_listening` | `() → None` | Signal the capture thread to stop and join it. |
| `listen_once` | `() → str` | Record until silence and return the transcribed text. |
| `on_command` | `(callback: Callable[[str], None]) → None` | Register a callback to receive transcribed commands. |
| `transcribe_audio` | `(audio_file: str) → Optional[str]` | Transcribe a WAV file path; returns cleaned text or `None`. |
| `get_events` | `() → List[Tuple[str, Optional[str]]]` | Drain and return queued `("command", text)` or `("error", msg)` events. |
| `is_listening` *(property)* | `→ bool` | `True` while the capture thread is running. |

### `TTSManager`

Manages text-to-speech synthesis and audio playback.

| Method | Signature | Description |
|---|---|---|
| `speak` | `(text: str, priority="normal") → None` | Synthesize and play `text` **synchronously** (blocks until done). |
| `speak_async` | `(text: str, priority="normal") → None` | Queue `text` for playback without blocking the caller. |
| `synthesize` | `(text: str) → str` | Synthesize `text` to a temporary WAV file; returns the file path. |
| `interrupt_and_speak` | `(text: str) → None` | Stop current speech immediately and speak `text` at urgent priority. |
| `is_speaking` *(property)* | `→ bool` | `True` while a speech request is being processed. |

### Module-level convenience functions

These wrap the module-level default `TTSManager` instance — use them instead of
instantiating `TTSManager` yourself for typical usage.

| Function | Signature | Description |
|---|---|---|
| `speak` | `(text: str) → None` | Synchronous TTS. Blocks until playback completes. |
| `speak_async` | `(text: str) → None` | Asynchronous TTS. Returns immediately. |
| `synthesize` | `(text: str) → str` | Returns path to a generated WAV file without playing it. |
| `contains_wake_word` | `(text: str, wake_words: Optional[List[str]] = None) → bool` | Returns `True` if `text` contains any of the wake words (case-insensitive substring match). |

---

## Voice Command Flow

Step-by-step when the user says **"Add task to learn Docker"**:

1. **Microphone** — `VoiceInputManager._record_until_silence()` captures audio frames.
2. **Transcription** — `VoiceInputManager.transcribe_audio()` calls Whisper locally; returns
   `"Add task to learn Docker"`.
3. **Callback invoked** — for each registered callback,  
   `callback("Add task to learn Docker")` is called.
4. **Voice Adapter** — `voice_command_callback()` in `adapters/voice_adapter.py` receives the
   text and calls `execute_command("Add task to learn Docker")`.
5. **Command Executor** — parses intent (`add_task`), routes to `handle_add_task()`, returns:
   ```python
   {"status": "success", "reply": "Added task: learn Docker", "payload": {...}, "intent": "add_task"}
   ```
6. **Voice Adapter** — extracts `reply`, calls `format_for_voice()` (strips markdown), then
   calls `speak("Added task: learn Docker")`.
7. **TTS** — `TTSManager` synthesizes and plays the reply through the speakers.

---

## API Command Flow

Step-by-step when `POST /execute {"message": "Add task to learn Docker"}` is called:

1. **HTTP request** — FastAPI receives the request in `api/routes.py`.
2. **Route handler** — `execute()` extracts `request.message` and calls  
   `execute_command("Add task to learn Docker")`.
3. **Command Executor** — same logic as the voice path; returns the same response dict.
4. **Route handler** — returns the dict directly; FastAPI serializes it to JSON:
   ```json
   {"status": "success", "reply": "Added task: learn Docker", "payload": {...}, "intent": "add_task"}
   ```
5. **HTTP response** — the client receives `200 OK` with the JSON body.

The voice module is **not involved at any point** in the API flow.

---

## Voice Adapter Pattern

`adapters/voice_adapter.py` is the **single integration point** between the voice module
and the rest of the application. It is the *only* file that imports from both `voice/` and
`core/command_executor`.

### Why a separate adapter?

- Keeps `voice/` free of business-logic dependencies (no managers, no HTTP, no intent parsing).
- Keeps `core/command_executor.py` free of voice dependencies (no `speak()`, no audio).
- Future interfaces (GUI, CLI, mobile) can follow the same pattern without touching either module.

### Registering the callback

```python
# In main.py or application startup
from voice import VoiceInputManager
from adapters.voice_adapter import voice_command_callback

voice_manager = VoiceInputManager(model_name="small")
voice_manager.on_command(voice_command_callback)
voice_manager.start_listening()
```

`voice_command_callback` is a plain Python function with the signature
`(command_text: str) -> None`. It is passed to `on_command()` and called automatically
each time Whisper produces a transcription.

---

## Wake Word Detection

```python
from voice import contains_wake_word

# Default wake words: ["jarvis", "assistant", "hey nova"]
contains_wake_word("hey jarvis, what time is it")  # True
contains_wake_word("hello world")                   # False

# Custom wake words
contains_wake_word("ok nova, open browser", wake_words=["ok nova", "hey nova"])  # True
```

`contains_wake_word(text, wake_words=None) → bool`

- Performs a **case-insensitive substring search** — no ML model needed for V1.
- `wake_words` defaults to `["jarvis", "assistant", "hey nova"]` when `None`.
- Returns `True` as soon as any wake word is found.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `VOICE_MODEL` | `"base"` | Whisper model size. Options: `tiny`, `base`, `small`, `medium`, `large`. Larger = more accurate, slower load. |
| `WAKE_WORDS` | `"jarvis,assistant"` | Comma-separated list of wake words read at startup. |
| `SAMPLE_RATE` | `16000` | Audio sample rate in Hz. |

Set via environment variables or override in `config.py`:

```bash
export VOICE_MODEL=small
export WAKE_WORDS="jarvis,hey nova,assistant"
```

Or pass directly at construction time:

```python
manager = VoiceInputManager(model_name="small", wake_words=["jarvis", "hey nova"])
```

---

## Quick Start

```python
from voice import VoiceInputManager
from adapters.voice_adapter import voice_command_callback

# Create manager — uses "small" Whisper model by default
voice_manager = VoiceInputManager(model_name="small")

# Register the adapter callback (bridges voice → command executor → speak)
voice_manager.on_command(voice_command_callback)

# Start listening in a background thread
voice_manager.start_listening(background=True)

print("Listening… say 'jarvis' followed by a command.")

# Later, when shutting down:
# voice_manager.stop_listening()
```

If you only need TTS without microphone input:

```python
from voice import speak, speak_async

speak("Hello! I am your assistant.")          # blocks until done
speak_async("Processing your request...")     # returns immediately
```

---

## Dependency Rules (must not be violated)

```
voice/*              MUST NOT import from  core/, handlers/, managers/, services/, api/
core/command_executor.py  MUST NOT import from  voice/
adapters/voice_adapter.py  is the ONLY file allowed to import from both voice/ and core/
```

Violating these rules reintroduces the circular dependency the refactor was designed to eliminate.
