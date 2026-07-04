# Project Structure

```text
ai-backend/
│
├── main.py                         # FastAPI app entry point; registers routes, DB, and voice adapter callback
├── run_voice.py                    # Standalone script to start the voice assistant (mic listening loop)
├── config.py                       # App-wide config: VOICE_MODEL, OLLAMA_URL, OLLAMA_MODEL from env vars
├── requirements.txt                # Python package dependencies
├── structure.md                    # This file — project layout and file descriptions
├── MIGRATION_GUIDE.md              # Documents the 13-phase voice-API separation migration strategy
│
├── api/
│   ├── __init__.py
│   └── routes.py                   # FastAPI route definitions: /execute, /chat, /tasks, /intent endpoints
│
├── core/
│   ├── __init__.py
│   ├── command_executor.py         # Central routing layer: parses intent and dispatches to correct handler
│   ├── response_builder.py         # Factory helpers: success(), error(), partial() for standardized response dicts
│   ├── intent_parser.py            # Rule-based NLP: extracts intent + entities (app, task, url, etc.) from raw text
│   ├── intent_router.py            # Legacy router module (superseded by HANDLERS dict in command_executor)
│   ├── conversation.py             # Conversation history management for multi-turn context
│   ├── memory.py                   # Short-term in-memory storage for session state
│   └── prompt_builder.py           # Builds LLM prompt strings with system context and conversation history
│
├── handlers/
│   ├── __init__.py                 # Re-exports all handler functions for convenient imports
│   ├── task_handler.py             # Handles add_task, show_tasks, complete_task, show_stats, update_task intents
│   ├── browser_handler.py          # Handles open_website and search_web intents (opens browser/Google search)
│   ├── app_handler.py              # Handles open_application and close_application intents (desktop apps)
│   ├── system_handler.py           # Handles lock_pc, take_screenshot, and volume_control intents
│   ├── media_handler.py            # Handles play_music and media_control intents (play/pause/next/previous)
│   └── chat_handler.py             # Handles general_chat and answer_question intents via Ollama LLM fallback
│
├── adapters/
│   ├── __init__.py
│   └── voice_adapter.py            # ONLY module that imports both voice/ and command_executor; bridges mic → executor → TTS
│
├── voice/
│   ├── __init__.py                 # Public API exports: VoiceInputManager, TTSManager, speak, speak_async, contains_wake_word
│   ├── README.md                   # Documents the three-layer architecture and voice module usage
│   ├── stt.py                      # VoiceInputManager: mic capture, Whisper transcription, callback dispatch
│   ├── tts.py                      # TTSManager: pyttsx3-based TTS with priority queue and dedicated worker thread
│   └── wake_word.py                # contains_wake_word(): simple substring-based wake word detection
│
├── managers/
│   ├── __init__.py
│   ├── app_manager.py              # Launches and closes desktop apps; loads Start Menu app cache on startup
│   ├── browser_manager.py          # Opens URLs and websites in the default browser
│   ├── media_manager.py            # Controls media playback (play by search query)
│   ├── system_manager.py           # OS-level actions: lock screen, screenshot, volume mute/unmute/up/down
│   ├── task_manager.py             # Re-exports CRUD operations from task_repository (thin pass-through layer)
│   └── window_manager.py           # Window management: minimize, maximize, focus, close windows by title
│
├── services/
│   ├── __init__.py
│   ├── llm_service.py              # High-level LLM interface: re-exports OllamaClient and send_message
│   ├── ollama_service.py           # Ollama API client: sends messages and streams responses from local LLM
│   └── whisper_service.py          # Whisper model wrapper for standalone audio file transcription
│
├── database/
│   ├── __init__.py                 # Exports init_db() to set up SQLite schema on first run
│   ├── db.py                       # SQLite connection setup and session management
│   ├── models.py                   # TaskRecord dataclass: id, task_name, date, category, priority, completed, timestamps
│   └── task_repository.py          # Raw DB queries for task CRUD: add, get, complete, delete, find, stats
│
├── utils/
│   ├── __init__.py
│   ├── constants.py                # Shared constants: known app names, website aliases, intent keywords
│   ├── entity_matcher.py           # Fuzzy matching helpers for website names and app names
│   ├── logger.py                   # Shared application logger configuration
│   └── transcript_corrector.py     # Post-processes Whisper transcripts to fix common misrecognitions
│
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py            # Unit tests for all handler modules with mocked manager calls
│   ├── test_response_builder.py    # Unit tests for success(), error(), partial() response helpers
│   ├── test_voice_adapter.py       # Integration tests for voice_command_callback pipeline
│   ├── test_api_routes.py          # Integration tests for /execute, /chat FastAPI endpoints
│   ├── test_wake_word.py           # Unit tests for contains_wake_word() detection function
│   ├── test_intent.py              # Unit tests for intent parsing and entity extraction
│   ├── test_intent_detection.py    # Additional intent detection edge case tests
│   ├── test_router.py              # Tests for intent routing to correct handler
│   ├── test_task_handlers.py       # Task handler tests with DB interactions
│   ├── test_task_handlers_direct.py # Direct task handler call tests without full pipeline
│   ├── test_task_migration.py      # Tests verifying task handler behavior after migration
│   ├── test_app_handlers.py        # App open/close handler unit tests
│   ├── test_app_handlers_integration.py # Integration tests for app launching
│   ├── test_browser.py             # Browser handler and URL opening tests
│   ├── test_phase3_browser.py      # Browser handler phase 3 migration tests
│   ├── test_media_handler.py       # Media handler unit tests
│   ├── test_media_integration.py   # Media playback integration tests
│   ├── test_system_commands_phase5.py # System handler phase 5 migration tests
│   ├── test_phase5_system.py       # Additional system command tests
│   ├── test_phase2_final.py        # Final validation tests for phase 2 migration
│   ├── test_tts.py                 # TTS engine initialization and speech output tests
│   ├── test_voice.py               # VoiceInputManager mic capture and transcription tests
│   ├── test_volume.py              # Volume control (mute/unmute/up/down) tests
│   ├── test_lock.py                # Lock PC functionality tests
│   ├── test_window.py              # Window manager tests
│   ├── debug_volume.py             # Debug script for diagnosing volume control issues
│   ├── check_schema.py             # Script to inspect and verify the SQLite database schema
│   ├── clear_tasks.py              # Utility script to wipe all tasks from the database
│   ├── run_phase7_tests.py         # Test runner for phase 7 migration tests
│   ├── phase7_test2.py             # Phase 7 migration test variant 2
│   ├── phase7_test3.py             # Phase 7 migration test variant 3
│   ├── phase7_test4.py             # Phase 7 migration test variant 4
│   └── test.py                     # General scratch/exploratory test file
│
├── data/
│   ├── nova.db                     # SQLite database file storing tasks and app data
│   └── screenshots/                # Directory where taken screenshots are saved
│
└── logs/                           # Directory for application log files (auto-created at runtime)
```

---

## Detailed File Descriptions

### Entry Points

**`main.py`** — FastAPI application factory. Creates the `FastAPI` app instance titled "Jarvis AI", calls `init_db()` to ensure the SQLite schema exists, and registers all HTTP routes via `app.include_router(router)`. On startup, it calls `load_start_menu_apps()` to pre-cache all installed Windows apps. Also exposes `setup_voice(voice_manager)` — a helper that wires the `voice_command_callback` into any `VoiceInputManager` instance, keeping voice setup decoupled from the HTTP server.

**`run_voice.py`** — Standalone voice-mode entry point. Initialises the database, loads the app cache, pre-warms the TTS worker thread so pyttsx3 COM initialisation happens immediately (not mid-command), then creates a `VoiceInputManager` with the configured Whisper model, registers `voice_command_callback`, and calls `start_listening(background=False)` to block forever in the mic loop. Includes a `KeyboardInterrupt` handler for clean shutdown.

**`config.py`** — Central configuration via environment variables. Reads three values at import time: `VOICE_MODEL` (Whisper model size, default `"medium"`), `OLLAMA_URL` (local LLM endpoint, default `"http://localhost:11434"`), and `OLLAMA_MODEL` (which Ollama model to use, default `"qwen3:8b"`). All modules that need config import from here rather than reading env vars directly.

---

### `api/` — HTTP Interface Layer

**`routes.py`** — Defines all FastAPI endpoints using a shared `APIRouter`. Routes:
- `GET /` — health check, returns `{"status": "Jarvis Online"}`
- `POST /chat` — backward-compatible endpoint, calls `execute_command(message)` directly
- `POST /execute` — primary command endpoint, also calls `execute_command(message)`; accepts optional `task_id`
- `POST /intent` — debug endpoint that runs `parse_intent()` and returns raw intent + entities + confidence without executing anything
- `GET /tasks` — returns all tasks from the database
- `GET /tasks/stats` — returns pending/completed task counts
- `DELETE /tasks` — deletes a task by `task_id`

Both `/chat` and `/execute` are functionally equivalent — both call `execute_command()` and return its response dict as JSON.

---

### `core/` — Business Logic Layer

**`command_executor.py`** — The single entry point for all command processing regardless of origin (voice, HTTP, CLI, tests). The `execute_command(command, context)` function: (1) calls `parse_intent()` to extract intent name and entities; (2) injects the raw command string into `context["raw_command"]`; (3) looks up the handler in the `HANDLERS` dict (16 intents registered); (4) calls the handler with `(entities, context)`; (5) stamps the `intent` key onto the response for debugging; (6) catches all exceptions and returns a safe error dict. The `HANDLERS` dict maps every supported intent string to its handler callable — no if/elif chain needed.

**`intent_parser.py`** — Rule-based NLP pipeline. `parse_intent(text)` normalises input to lowercase, then runs a priority-ordered chain of `re.search()` checks to assign one of 16 intents. Entity extraction is handled by private helpers: `_extract_task_name()` (regex against intent-specific patterns), `_extract_url()` (URL regex + known website alias matching), `_extract_search_query()` (Google/search pattern matching), `_extract_application()` (substring scan against `KNOWN_APPS` list), `_extract_volume_action()` / `_extract_media_action()` (keyword checks), `_extract_priority()`, `_extract_category()`, `_extract_date()`. Returns `{"intent", "entities", "confidence"}` where confidence is a heuristic float (0.5–0.95) based on whether key entities were found.

**`response_builder.py`** — Lightweight factory module. Three functions — `success(reply, payload, metadata)`, `error(reply, payload, metadata)`, `partial(reply, payload, metadata)` — each return a consistently structured dict with a `status` key (`"success"`, `"error"`, `"partial"`), a `reply` string for the user, and optional `payload` and `metadata` dicts. Every handler uses these rather than constructing raw dicts, ensuring consistent response shape across all code paths.

**`conversation.py`** — `ConversationManager` class backed by a `collections.deque` with a configurable max length (default 20 messages). Stores alternating `user`/`assistant` message dicts. Provides `add_user()`, `add_assistant()`, `get_history()`, and `clear()`. Currently instantiated but not yet wired into the main command pipeline — available for multi-turn conversation context when needed.

**`prompt_builder.py`** — Builds structured prompt strings for the LLM. Prepends a system context block and injects conversation history before the current user message, giving the LLM context about prior turns.

**`memory.py`** — In-memory key/value store for session state within a single run. Not persisted to disk.

**`intent_router.py`** — Legacy routing module kept for reference. Its logic has been superseded by the `HANDLERS` dict in `command_executor.py`.

---

### `handlers/` — Intent Handler Layer

All handlers follow the same contract: `handle_*(entities: dict, context: dict | None) -> ResponseDict`. They have **no voice imports** and **no HTTP framework imports** — they are pure business logic.

**`task_handler.py`** — Five handlers for task management:
- `handle_add_task` — reads `task_name`, `date`, `category`, `priority` from entities; calls `add_task()` from `task_manager`; returns the created task object in `payload`.
- `handle_show_tasks` — calls `get_tasks(include_completed)`; formats each task with a ✓/○ status icon and optional due date; returns the full task list in `payload["tasks"]`.
- `handle_complete_task` — accepts either `task_name` or `task_id` as identifier; calls `complete_task()`; returns the updated task in `payload`.
- `handle_show_stats` — calls `get_task_stats()`; formats a human-readable summary (`"N pending and M completed tasks"`).
- `handle_update_task` — stub, returns a placeholder reply (not yet implemented).

**`browser_handler.py`** — Two handlers: `handle_open_website` opens a URL (from `entities["url"]`) in the default browser via `browser_manager`; `handle_search_web` constructs a Google search URL from `entities["search_query"]` and opens it.

**`app_handler.py`** — Two handlers: `handle_open_application` looks up the app name from `entities["app_name"]` and calls `app_manager.open_app()`; `handle_close_application` calls `app_manager.close_app()`.

**`system_handler.py`** — Three handlers: `handle_lock_pc` calls `system_manager.lock_screen()`; `handle_screenshot` calls `system_manager.take_screenshot()` and returns the saved file path; `handle_volume_control` reads `entities["volume_action"]` (`mute`/`unmute`/`up`/`down`) and calls the corresponding `system_manager` function.

**`media_handler.py`** — Two handlers: `handle_play_music` reads `entities["media_query"]` and calls `media_manager.play(query)`; `handle_media_control` reads `entities["media_action"]` and dispatches to pause/resume/next/previous controls.

**`chat_handler.py`** — Single handler `handle_general_chat`, used as both the explicit chat handler and the fallback for any unrecognised intent. Reads `context["raw_command"]`, streams a response from Ollama via `ollama_service.send_message()`, joins all chunks, and returns the result. Handles `OllamaConnectionError` (service not running) and empty-reply cases with distinct error messages.

---

### `adapters/` — Integration Bridge

**`voice_adapter.py`** — The **sole** file allowed to import from both `voice/` and `core/`. Contains two functions:
- `format_for_voice(text)` — strips markdown formatting (fenced code blocks, inline code, bold/italic markers, link syntax, heading markers, list bullets) and collapses whitespace so the output sounds natural when read by TTS.
- `voice_command_callback(command_text)` — registered as the `on_command` callback on `VoiceInputManager`. Validates non-empty input, calls `execute_command()`, extracts `reply` and `status` from the response, applies `format_for_voice()`, and calls `speak()`. Any exception is caught and spoken as a fallback error message so the user always hears audio feedback.

---

### `voice/` — Audio I/O Layer

Handles all audio concerns and nothing else. Has **no imports from `core/`, `handlers/`, or `managers/`**.

**`stt.py`** — `VoiceInputManager`: captures mic audio, runs Whisper transcription in a background thread, and dispatches the transcript string to the registered callback. The Whisper model loads lazily when `start_listening()` is first called (takes 1–3 min on first run). Supports both blocking and non-blocking listening modes.

**`tts.py`** — `TTSManager`: wraps pyttsx3 with a thread-safe priority queue and a dedicated worker thread. All `speak()` calls are serialised through this queue so TTS never blocks the main thread or the voice callback thread. `_default_tts_manager` is a module-level singleton pre-warmed at startup.

**`wake_word.py`** — `contains_wake_word(text)`: simple case-insensitive substring check against a configurable wake word list. Used to filter transcripts before dispatching as commands.

---

### `managers/` — OS & Resource Manager Layer

Thin wrappers around OS-level operations. Called only by handlers, never directly by API routes or voice code.

**`app_manager.py`** — Caches all Start Menu `.lnk` shortcuts at startup into a dict keyed by lowercased app name. `open_app(name)` does a fuzzy lookup against the cache and launches the app; `close_app(name)` finds matching windows and closes them.

**`browser_manager.py`** — Calls `webbrowser.open(url)` for website opening. Handles URL normalisation (adds `https://` prefix when missing).

**`media_manager.py`** — Uses platform media keys or search-based launching (e.g., opens Spotify search URL) to control media playback.

**`system_manager.py`** — OS-level actions using `ctypes` / `subprocess`: `lock_screen()` calls the Windows lock API, `take_screenshot()` uses `PIL.ImageGrab` and saves to `data/screenshots/`, and volume functions use `pycaw` or `nircmd` for mute/unmute/up/down.

**`task_manager.py`** — A thin re-export shim that publishes `add_task`, `complete_task`, `delete_task`, `find_task`, `get_task_stats`, `get_tasks`, `update_task` from `database.task_repository`. Handlers import from `managers.task_manager` rather than directly from `database` to maintain layer separation.

**`window_manager.py`** — Uses `pygetwindow` to enumerate open windows, match by title substring, and perform minimize/maximize/focus/close operations.

---

### `services/` — External Service Clients

**`ollama_service.py`** — `OllamaClient` class and `send_message(text)` generator function. Posts messages to the Ollama HTTP API (`/api/chat`) and yields response chunks as they stream in. Raises `OllamaConnectionError` (a custom exception) when the service is unreachable, so handlers can present a user-friendly message without catching raw `requests` exceptions.

**`whisper_service.py`** — Standalone wrapper for transcribing a pre-recorded audio file with Whisper. Used for batch transcription scenarios outside the real-time mic loop.

**`llm_service.py`** — Re-exports `OllamaClient`, `send_message`, and `parse_intent` as a unified LLM service surface.

---

### `database/` — Persistence Layer

**`db.py`** — Creates and manages a SQLite connection using the path `data/nova.db`. Provides a `get_connection()` helper and manages schema initialisation.

**`models.py`** — `TaskRecord` dataclass with fields: `id` (int), `task_name` (str), `date` (optional str), `category` (optional str), `priority` (optional str), `completed` (bool, default False), `created_at` and `updated_at` timestamps.

**`task_repository.py`** — All raw SQL for task operations: `add_task()` inserts a new row and returns the created `TaskRecord` as a dict; `get_tasks(include_completed)` returns a list of task dicts; `complete_task(identifier)` updates `completed=True` by name or ID; `delete_task(task_id)` removes by ID; `find_task(identifier)` does a name/ID lookup; `get_task_stats()` returns `{"pending": N, "completed": M, "total": T}`.

---

### `utils/` — Shared Utilities

**`constants.py`** — Single source of truth for string constants: the `KNOWN_APPS` list used by the intent parser, website alias mappings (e.g., `"youtube"` → `"https://youtube.com"`), and intent keyword sets.

**`entity_matcher.py`** — `match_website(text)` uses `difflib.get_close_matches` for fuzzy website name resolution. Also provides app name fuzzy matching used when a substring match in `KNOWN_APPS` is insufficient.

**`logger.py`** — Configures a module-level `logging.Logger` with consistent format and log level. All modules obtain their logger via `logging.getLogger(__name__)`.

**`transcript_corrector.py`** — Post-processes raw Whisper output to fix recurring misrecognitions (e.g., "nova" misheard as "nova", punctuation artifacts). Applied before the transcript reaches the intent parser.

---

## Architecture Overview

This project follows a **three-layer architecture** to cleanly separate voice I/O from business logic:

```
Input Layer          Core Layer              Output Layer
────────────         ──────────              ────────────
voice/stt.py    →    command_executor   →    voice/tts.py  (via voice_adapter)
api/routes.py   →    + handlers/*       →    JSON response (via FastAPI)
```

**Key dependency rule**: `voice/` and `core/` never import each other. `adapters/voice_adapter.py` is the **only** module allowed to import both, acting as the integration bridge.

---

## Project Working Flow

This section describes exactly what happens from the moment a user speaks a command (or sends an HTTP request) to the moment a response is returned.

### Mode A — Voice Mode (run_voice.py)

```
Microphone
    │
    ▼
voice/stt.py :: VoiceInputManager
    │  Captures raw PCM audio chunks from the mic
    │  Runs Whisper model in a background thread
    │  Produces a transcript string (e.g. "Add task to learn Docker")
    │
    ▼  [on_command callback fires]
adapters/voice_adapter.py :: voice_command_callback(command_text)
    │  Validates non-empty input
    │  Calls execute_command(command_text)
    │         ↓ (see Core Pipeline below)
    │  Receives ResponseDict back
    │  Extracts reply string
    │  Calls format_for_voice(reply) → strips markdown
    │
    ▼
voice/tts.py :: speak(cleaned_reply)
    │  Enqueues reply in TTS priority queue
    │  Dedicated worker thread picks it up
    │  pyttsx3 synthesises and plays audio
    ▼
User hears the response
```

**Startup sequence (run_voice.py):**
1. `init_db()` — ensures `data/nova.db` schema exists
2. `load_start_menu_apps()` — scans Windows Start Menu, builds app name → path cache
3. `_default_tts_manager._ensure_worker()` — pre-warms pyttsx3 COM initialisation
4. `VoiceInputManager(model_name=VOICE_MODEL)` — creates manager (Whisper loads when listening starts)
5. `vm.on_command(voice_command_callback)` — registers the adapter callback
6. `vm.start_listening(background=False)` — blocks; Whisper model downloads/loads, then mic opens

---

### Mode B — HTTP API Mode (main.py + uvicorn)

```
HTTP Client
    │  POST /execute  {"message": "Add task to learn Docker"}
    ▼
api/routes.py :: execute(request)
    │  Extracts request.message
    │  Calls execute_command(message)
    │         ↓ (see Core Pipeline below)
    │  Receives ResponseDict
    ▼
FastAPI serialises dict → JSON response to client
```

**Startup sequence (main.py):**
1. `FastAPI` app is created
2. `init_db()` — ensures schema exists
3. `app.include_router(router)` — mounts all routes
4. On first request: `startup_event()` fires → `load_start_menu_apps()`

---

### Core Pipeline — execute_command(command, context)

Both voice mode and HTTP mode converge here. This pipeline runs identically regardless of caller.

```
execute_command("Add task to learn Docker")
    │
    ├─ Step 1: Intent Parsing
    │     core/intent_parser.py :: parse_intent(command)
    │     │  Normalises text to lowercase
    │     │  Runs regex priority chain → assigns intent = "add_task"
    │     │  Runs entity extractors:
    │     │     _extract_task_name()   → "learn Docker"
    │     │     _extract_priority()    → None
    │     │     _extract_category()    → None
    │     │     _extract_date()        → None
    │     │     _extract_url()         → None
    │     │     _extract_application() → None
    │     │     ... (all other extractors return None)
    │     │  Assigns confidence = 0.9 (intent + task_name found)
    │     └─ Returns {"intent": "add_task", "entities": {...}, "confidence": 0.9}
    │
    ├─ Step 2: Context Injection
    │     Injects raw command string into context["raw_command"]
    │     (Used by chat_handler as fallback for LLM queries)
    │
    ├─ Step 3: Handler Lookup
    │     HANDLERS["add_task"] → handle_add_task
    │     (Falls back to handle_general_chat for unknown intents)
    │
    ├─ Step 4: Handler Execution
    │     handlers/task_handler.py :: handle_add_task(entities, context)
    │     │  Reads entities["task_name"] = "learn Docker"
    │     │  Calls managers/task_manager.add_task(task_name, date, category, priority)
    │     │        ↓
    │     │        database/task_repository.py :: add_task(...)
    │     │        │  Inserts row into SQLite nova.db
    │     │        └─ Returns TaskRecord dict {"id": 42, "task_name": "learn Docker", ...}
    │     └─ Returns success("Added task: learn Docker", payload=task_dict)
    │           = {"status": "success", "reply": "Added task: learn Docker", "payload": {...}}
    │
    └─ Step 5: Intent Stamping
          Adds "intent": "add_task" to the response dict
          Returns final ResponseDict to caller
```

---

### LLM Fallback Flow (general_chat / answer_question)

When no specific intent is matched, or when a question is asked directly:

```
execute_command("What is the capital of France?")
    │
    ├─ parse_intent() → intent = "answer_question", entities = {}
    ├─ HANDLERS["answer_question"] → handle_general_chat
    │
    └─ handlers/chat_handler.py :: handle_general_chat(entities, context)
          │  Reads context["raw_command"] = "What is the capital of France?"
          │  Calls services/ollama_service.send_message(raw_command)
          │        │  HTTP POST to http://localhost:11434/api/chat
          │        │  Streams response chunks
          │        └─ Generator yields text chunks
          │  Joins chunks → full reply string
          └─ Returns success(reply)
```

If Ollama is not running, `OllamaConnectionError` is caught and a user-friendly
error reply is returned instead of propagating the exception.

---

### Intent Detection Decision Tree

The `parse_intent()` function evaluates conditions in this priority order:

```
Input text (lowercased)
    │
    ├─ contains "complete"/"finish"/"done"/"mark done"       → complete_task
    ├─ contains "update"/"edit"/"change"/"modify"            → update_task
    ├─ contains "add"/"create"/"new task"/"remember to"      → add_task / reminder
    ├─ show/list + "task" keyword combo                      → show_tasks
    ├─ contains "stats"/"statistics"/"progress"/"summary"   → show_stats
    ├─ contains "search"/"google"/"look up" + has query      → search_web
    ├─ contains "close"/"exit"/"quit"/"terminate"            → close_application
    ├─ _extract_application() returns a match               → open_application
    ├─ _extract_url() returns a match or "open"/"browser"   → open_website
    ├─ contains "remind"/"reminder"                          → reminder
    ├─ contains "screenshot"/"capture screen"               → take_screenshot
    ├─ contains "lock pc"/"lock screen"/"lock computer"     → lock_pc
    ├─ contains "mute"/"unmute"/"volume up"/"volume down"   → volume_control
    ├─ contains "play"/"pause"/"resume"/"next"/"previous"   → media_control
    └─ (no match)                                            → answer_question
```

---

### Response Format

Every response flowing through the system — regardless of intent or handler — uses the same dict shape:

```python
{
    "status":  "success" | "error" | "partial",
    "reply":   "Human-readable text for the user",        # always present
    "intent":  "add_task",                                 # stamped by execute_command
    "payload": { ... },                                    # optional: task object, stats, etc.
    "metadata": { ... },                                   # optional: debug info, confidence
}
```

- Voice mode reads only `reply`, strips markdown via `format_for_voice()`, and speaks it
- HTTP mode returns the entire dict as JSON to the client
- `status="partial"` is used when an operation partially succeeded (e.g., 2 of 3 tasks completed)

---

### Data Flow Diagram (Full System)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Input Sources                           │
│                                                                  │
│  Microphone ──► voice/stt.py ──► voice_adapter.py ──┐          │
│                                                       │          │
│  HTTP Client ──► api/routes.py ──────────────────────┤          │
└───────────────────────────────────────────────────────┼──────────┘
                                                        │
                                                        ▼
                              ┌─────────────────────────────────┐
                              │   core/command_executor.py      │
                              │   execute_command(text)         │
                              │                                  │
                              │  ┌──────────────────────────┐   │
                              │  │  core/intent_parser.py   │   │
                              │  │  parse_intent(text)      │   │
                              │  └──────────────────────────┘   │
                              │           │                       │
                              │           ▼                       │
                              │  HANDLERS[intent] → handler()    │
                              └─────────────┬───────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────┐
              │                             │                          │
              ▼                             ▼                          ▼
    handlers/task_handler         handlers/chat_handler      handlers/system_handler
    handlers/browser_handler      (Ollama LLM fallback)      handlers/app_handler
    handlers/media_handler                 │                  handlers/...
              │                            │
              ▼                            ▼
    managers/task_manager        services/ollama_service
    managers/app_manager         (HTTP → Ollama API)
    managers/system_manager
    managers/browser_manager
              │
              ▼
    database/task_repository
    (SQLite nova.db)
              │
              └──────────────────────────────────────────────────────┐
                                                                      ▼
                              ┌─────────────────────────────────────────────┐
                              │             ResponseDict                     │
                              │  {"status", "reply", "intent", "payload"}   │
                              └────────────────┬────────────────────────────┘
                                               │
              ┌────────────────────────────────┴───────────────┐
              │                                                  │
              ▼                                                  ▼
   voice_adapter.py                                    api/routes.py
   format_for_voice(reply)                             Returns JSON
   speak(cleaned_reply)
              │
              ▼
   voice/tts.py → pyttsx3 → Audio output
```

---

## How to Run

**Voice assistant (mic mode):**
```cmd
.venv\Scripts\activate
python run_voice.py
```

**API server (HTTP mode):**
```cmd
.venv\Scripts\activate
uvicorn main:app --reload
```

**Tests:**
```cmd
python -m pytest tests/ -v
```
