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
│   ├── command_executor.py         # Public entry point: splits chains, routes single commands via HANDLERS dict
│   ├── command_chain.py            # Command chaining: split_commands, _is_dependent, execute_chain
│   ├── execution_context.py        # ExecutionContext dataclass: shared state carrier between chained sub-commands
│   ├── response_builder.py         # Factory helpers: success(), error(), partial() for standardised response dicts
│   ├── intent_parser.py            # Rule-based NLP: extracts intent + entities from raw text
│   ├── intent_router.py            # Legacy router module (superseded by HANDLERS dict in command_executor)
│   ├── conversation.py             # Conversation history management for multi-turn context
│   ├── memory.py                   # Short-term in-memory storage for session state
│   └── prompt_builder.py           # Builds LLM prompt strings with system context and conversation history
│
├── handlers/
│   ├── __init__.py                 # Re-exports all handler functions for convenient imports
│   ├── task_handler.py             # Handles add_task, show_tasks, complete_task, show_stats, update_task intents
│   ├── browser_handler.py          # Handles open_website and search_web intents
│   ├── app_handler.py              # Handles open_application and close_application intents
│   ├── system_handler.py           # Handles lock_pc, take_screenshot, and volume_control intents
│   ├── media_handler.py            # Handles play_music and media_control intents
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
│   └── whisper_service.py          # Alias shim: re-exports VoiceInputManager as WhisperService
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
│   ├── entity_matcher.py           # match_website(): difflib fuzzy matching for website names
│   ├── logger.py                   # Shared application logger configuration
│   └── transcript_corrector.py     # LLM-based transcript cleanup: sends Whisper output to Ollama to fix misrecognitions
│
├── tests/
│   ├── __init__.py
│   ├── test_command_chain.py       # Unit + property-based tests for split_commands, _is_dependent, _update_context, execute_chain
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
│   ├── PHASE2_TEST_RESULTS.md      # Recorded test results for phase 2
│   ├── PHASE3_TEST_RESULTS.md      # Recorded test results for phase 3
│   ├── PHASE4_TEST_RESULTS.md      # Recorded test results for phase 4
│   ├── PHASE5_TEST_RESULTS.md      # Recorded test results for phase 5
│   ├── PHASE6_TEST_RESULTS.md      # Recorded test results for phase 6
│   ├── run_phase7_tests.py         # Test runner for phase 7 migration tests
│   ├── phase7_test2.py             # Phase 7 migration test variant 2
│   ├── phase7_test3.py             # Phase 7 migration test variant 3
│   ├── phase7_test4.py             # Phase 7 migration test variant 4
│   ├── debug_volume.py             # Debug script for diagnosing volume control issues
│   ├── check_schema.py             # Script to inspect and verify the SQLite database schema
│   ├── clear_tasks.py              # Utility script to wipe all tasks from the database
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

**`main.py`** — FastAPI application factory. Creates the `FastAPI` app instance titled "Jarvis AI", calls `init_db()` to ensure the SQLite schema exists, and registers all HTTP routes via `app.include_router(router)`. On startup calls `load_start_menu_apps()` to pre-cache all installed Windows apps. Also exposes `setup_voice(voice_manager)` to wire `voice_command_callback` into any `VoiceInputManager` instance, keeping voice setup decoupled from the HTTP server.

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

**`command_executor.py`** — The single public entry point for all command processing. `execute_command(command, context)` first calls `split_commands()` to detect chained input. If two or more sub-commands are found, it delegates to `execute_chain(commands, execute_single)` and returns a `Chain_Response`. For a single command it calls `execute_single()` directly and returns a standard `ResponseDict`. Also defines `handle_reminder()` (stub) and the `HANDLERS` dict mapping all 17 supported intent strings to their handler callables.

**`command_chain.py`** — Full command-chaining pipeline. Three public functions:
- `split_commands(text)` — splits a compound utterance at connector keywords (`and`, `then`, `also`, `after that`, `,`) while protecting quoted strings and URLs from being broken. Returns a list of trimmed sub-command strings.
- `execute_chain(commands, execute_fn)` — executes sub-commands sequentially, respecting dependency rules. Calls `execute_fn` (injected to avoid circular imports) for each non-skipped command, updates `ExecutionContext` after each step, and returns a `Chain_Response` with aggregated `status` (`success` / `partial` / `error`), combined `reply`, and a `payload` containing `executed_commands` and per-command `results`.
- Private helpers: `_is_dependent(cmd, prev_intent)` — detects pronoun references (`it`, `that`, `there`, `this app`, `this window`) and media-after-app patterns; `_update_context(ec, cmd, result)` — updates `last_app`, `last_window`, `last_website`, `last_intent`, `last_command` from the result dict.

**`execution_context.py`** — `ExecutionContext` dataclass. Carries shared state between sub-commands in a chain: `last_app`, `last_window`, `last_website`, `last_command`, `last_intent`. Initialised fresh at the start of every `execute_chain()` call. Has zero project imports (only `dataclasses` and `typing`) to stay at the bottom of the dependency graph and prevent circular imports.

**`intent_parser.py`** — Rule-based NLP pipeline. `parse_intent(text)` normalises input to lowercase, then runs a priority-ordered chain of `re.search()` checks to assign one of 16 intents. Entity extraction is handled by private helpers for task name, URL, search query, application name, volume/media actions, priority, category, and date. Returns `{"intent", "entities", "confidence"}` where confidence is a heuristic float (0.5–0.95).

**`response_builder.py`** — Lightweight factory module. `success()`, `error()`, `partial()` each return a consistently structured dict with a `status` key, a `reply` string, and optional `payload` and `metadata` dicts. Every handler uses these for consistent response shape.

**`conversation.py`** — `ConversationManager` class backed by a `collections.deque` (max 20 messages). Stores alternating `user`/`assistant` message dicts. Available for multi-turn context when needed.

**`prompt_builder.py`** — Builds structured prompt strings for the LLM. Prepends a system context block and injects conversation history before the current user message.

**`memory.py`** — In-memory key/value store for session state within a single run. Not persisted to disk.

**`intent_router.py`** — Legacy routing module kept for reference; superseded by the `HANDLERS` dict in `command_executor.py`.

---

### `handlers/` — Intent Handler Layer

All handlers follow the same contract: `handle_*(entities: dict, context: dict | None) -> ResponseDict`. They have **no voice imports** and **no HTTP framework imports**.

**`task_handler.py`** — Five handlers: `handle_add_task`, `handle_show_tasks`, `handle_complete_task`, `handle_show_stats`, `handle_update_task` (stub). Each is fully documented with docstrings, type hints, and usage examples.

**`browser_handler.py`** — `handle_open_website` opens a URL in the default browser; `handle_search_web` constructs a Google search URL from the query and opens it.

**`app_handler.py`** — `handle_open_application` and `handle_close_application` delegate to `app_manager`.

**`system_handler.py`** — `handle_lock_pc`, `handle_screenshot` (returns saved file path), `handle_volume_control` (mute/unmute/up/down).

**`media_handler.py`** — `handle_play_music` and `handle_media_control` (pause/resume/next/previous).

**`chat_handler.py`** — `handle_general_chat`: reads `context["raw_command"]`, streams a response from Ollama via `ollama_service.send_message()`, handles `OllamaConnectionError` and empty replies.

---

### `adapters/` — Integration Bridge

**`voice_adapter.py`** — The **sole** file allowed to import from both `voice/` and `core/`. Contains:
- `format_for_voice(text)` — strips markdown formatting so output sounds natural when read by TTS.
- `voice_command_callback(command_text)` — registered as the `on_command` callback on `VoiceInputManager`. Calls `execute_command()`, extracts `reply`, applies `format_for_voice()`, and calls `speak()`. Any exception is caught and spoken as fallback audio.

---

### `voice/` — Audio I/O Layer

Handles all audio concerns. Has **no imports from `core/`, `handlers/`, or `managers/`**.

**`stt.py`** — `VoiceInputManager`: captures mic audio, runs Whisper transcription in a background thread, dispatches transcript to the registered callback. Supports blocking and non-blocking modes.

**`tts.py`** — `TTSManager`: wraps pyttsx3 with a thread-safe priority queue and dedicated worker thread. All `speak()` calls are serialised so TTS never blocks the main thread.

**`wake_word.py`** — `contains_wake_word(text)`: case-insensitive substring check against a configurable wake word list.

---

### `managers/` — OS & Resource Manager Layer

Thin wrappers around OS-level operations. Called only by handlers.

**`app_manager.py`** — Caches Start Menu shortcuts at startup; fuzzy-launches and closes apps by name.

**`browser_manager.py`** — Calls `webbrowser.open(url)` with URL normalisation.

**`media_manager.py`** — Search-based media launching and playback control.

**`system_manager.py`** — `lock_screen()`, `take_screenshot()` (PIL), volume functions via `pycaw`/`nircmd`.

**`task_manager.py`** — Thin re-export shim: publishes `add_task`, `complete_task`, `delete_task`, `find_task`, `get_task_stats`, `get_tasks`, `update_task` from `database.task_repository`.

**`window_manager.py`** — Uses `pygetwindow` to minimise, maximise, focus, or close windows by title substring.

---

### `services/` — External Service Clients

**`ollama_service.py`** — `OllamaClient` and `send_message(text)` generator. Posts to Ollama HTTP API and yields response chunks. Raises `OllamaConnectionError` when the service is unreachable.

**`llm_service.py`** — Re-exports `OllamaClient`, `send_message`, and `parse_intent` as a unified LLM service surface.

**`whisper_service.py`** — Alias shim only: re-exports `VoiceInputManager` from `voice.stt` as `WhisperService` for backward compatibility. Contains no standalone logic.

---

### `database/` — Persistence Layer

**`db.py`** — SQLite connection to `data/nova.db`. Provides `get_connection()` and manages schema initialisation.

**`models.py`** — `TaskRecord` dataclass: `id`, `task_name`, `date`, `category`, `priority`, `completed` (bool), `created_at`, `updated_at`.

**`task_repository.py`** — All raw SQL for task operations: `add_task()`, `get_tasks()`, `complete_task()`, `delete_task()`, `find_task()`, `get_task_stats()`.

---

### `utils/` — Shared Utilities

**`constants.py`** — `KNOWN_APPS` list, website alias mappings, and intent keyword sets.

**`entity_matcher.py`** — `match_website(name)`: uses `difflib.get_close_matches` (cutoff 0.75) against `KNOWN_WEBSITES` to resolve fuzzy website names. Returns the best match string or `None`.

**`logger.py`** — Configures a module-level `logging.Logger` with consistent format and log level.

**`transcript_corrector.py`** — LLM-powered transcript cleanup. `cleanup_task_command(command)` sends the raw Whisper transcript to Ollama with a focused correction prompt (fix STT mistakes, preserve meaning, return only the corrected command). Falls back to the original command if the LLM call fails.

---

## Architecture Overview

This project follows a **three-layer architecture** to cleanly separate voice I/O from business logic:

```
Input Layer          Core Layer                        Output Layer
────────────         ──────────                        ────────────
voice/stt.py    →    command_executor                  voice/tts.py  (via voice_adapter)
api/routes.py   →      ├─ split_commands()         →   JSON response (via FastAPI)
                        ├─ execute_chain()
                        │     └─ execute_single() × N
                        └─ execute_single()
                              ├─ intent_parser
                              └─ HANDLERS[intent]
```

**Key dependency rules:**
- `voice/` and `core/` never import each other. `adapters/voice_adapter.py` is the **only** module allowed to import both.
- `core/command_chain.py` never imports from `core/command_executor.py` — the execute function is injected as a parameter to prevent circular imports.
- `core/execution_context.py` imports only from the Python standard library.

---

## Project Working Flow

### Mode A — Voice Mode (run_voice.py)

```
Microphone
    │
    ▼
voice/stt.py :: VoiceInputManager
    │  Captures PCM audio, runs Whisper in background thread
    │  Produces transcript string (e.g. "Open Spotify and play Shape of You")
    │
    ▼  [on_command callback fires]
adapters/voice_adapter.py :: voice_command_callback(command_text)
    │  Validates non-empty input
    │  Calls execute_command(command_text)
    │         ↓ (see Core Pipeline below)
    │  Receives ResponseDict or Chain_Response
    │  Extracts reply string
    │  Calls format_for_voice(reply) → strips markdown
    │
    ▼
voice/tts.py :: speak(cleaned_reply)
    │  Enqueues reply in TTS priority queue
    │  Dedicated worker thread synthesises and plays audio
    ▼
User hears the response
```

---

### Mode B — HTTP API Mode (main.py + uvicorn)

```
HTTP Client
    │  POST /execute  {"message": "Open Chrome and search openai"}
    ▼
api/routes.py :: execute(request)
    │  Extracts request.message
    │  Calls execute_command(message)
    │         ↓ (see Core Pipeline below)
    │  Receives ResponseDict or Chain_Response
    ▼
FastAPI serialises dict → JSON response to client
```

---

### Core Pipeline — execute_command(command, context)

Both modes converge here. The pipeline now handles both single commands and chained commands.

```
execute_command("Open Spotify and play Shape of You")
    │
    ├─ Step 1: Chain Detection
    │     core/command_chain.py :: split_commands(command)
    │     │  Protects quoted strings and URLs from being split
    │     │  Splits on "and", "then", "also", "after that", ","
    │     └─ Returns ["Open Spotify", "play Shape of You"]  ← 2 sub-commands found
    │
    ├─ Step 2: Chain Execution (len >= 2)
    │     core/command_chain.py :: execute_chain(commands, execute_single)
    │     │
    │     │  Sub-command 1: "Open Spotify"
    │     │  ├─ _is_dependent("Open Spotify", None) → False
    │     │  ├─ execute_single("Open Spotify", ctx)
    │     │  │     parse_intent → intent="open_application", entities={"app_name": "spotify"}
    │     │  │     HANDLERS["open_application"] → handle_open_application
    │     │  │     Returns {"status": "success", "reply": "Opening Spotify", "intent": "open_application", ...}
    │     │  └─ _update_context(ec, "Open Spotify", result)
    │     │        ec.last_app = "spotify", ec.last_intent = "open_application"
    │     │
    │     │  Sub-command 2: "play Shape of You"
    │     │  ├─ _is_dependent("play Shape of You", "open_application")
    │     │  │     parse_intent → intent="play_music"  (media intent after open_application → True)
    │     │  ├─ prev_result.status == "success" → not skipped → execute
    │     │  ├─ execute_single("play Shape of You", ctx)
    │     │  │     parse_intent → intent="play_music", entities={"media_query": "Shape of You"}
    │     │  │     HANDLERS["play_music"] → handle_play_music
    │     │  │     Returns {"status": "success", "reply": "Playing Shape of You", ...}
    │     │  └─ _update_context(ec, ...)
    │     │
    │     └─ Status aggregation: 2 success, 0 error, 0 skipped → chain_status = "success"
    │
    └─ Returns Chain_Response:
          {
            "status": "success",
            "reply": "Opening Spotify and Playing Shape of You",
            "intent": "chain",
            "payload": {
              "executed_commands": ["Open Spotify", "play Shape of You"],
              "results": [...]
            }
          }
```

**Single-command path** (no connector found):
```
execute_command("Add task to learn Docker")
    │
    ├─ split_commands → ["Add task to learn Docker"]  ← single element
    │
    └─ execute_single("Add task to learn Docker", context)
          parse_intent → intent="add_task", entities={"task_name": "learn Docker", ...}
          HANDLERS["add_task"] → handle_add_task
          Returns {"status": "success", "reply": "Added task: learn Docker", ...}
```

---

### Dependency Skip Logic

When a dependent sub-command's prerequisite fails:

```
execute_chain(["open chrome", "maximize it"])
    │
    │  Sub-command 1: "open chrome" → status="error"
    │
    │  Sub-command 2: "maximize it"
    │  ├─ _is_dependent("maximize it", "open_application")
    │  │     pronoun "it" found → True
    │  ├─ prev_result.status == "error" → prereq_failed = True
    │  └─ SKIP — records:
    │         {"status": "skipped", "reply": "Could not complete 'open chrome', so 'maximize it' was skipped."}
    │
    └─ Status aggregation: 0 success, 1 error, 1 skipped → chain_status = "error"
```

---

### LLM Fallback Flow (general_chat / answer_question)

```
execute_command("What is the capital of France?")
    │
    ├─ split_commands → single command
    ├─ parse_intent → intent="answer_question"
    └─ handle_general_chat
          Reads context["raw_command"]
          Calls ollama_service.send_message(raw_command)
          Streams and joins response chunks
          Returns success(reply)
```

---

### Intent Detection Decision Tree

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

**Single-command `ResponseDict`:**
```python
{
    "status":  "success" | "error" | "partial",
    "reply":   "Human-readable text for the user",
    "intent":  "add_task",                           # stamped by execute_single
    "payload": { ... },                              # optional task object, stats, etc.
    "metadata": { ... },                             # optional debug info, confidence
}
```

**Multi-command `Chain_Response`:**
```python
{
    "status":  "success" | "partial" | "error",
    "reply":   "Opening Spotify and Playing Shape of You",   # joined with " and "
    "intent":  "chain",                                      # always "chain"
    "payload": {
        "executed_commands": ["Open Spotify", "play Shape of You"],
        "results": [
            {"status": "success", "reply": "Opening Spotify", "intent": "open_application", ...},
            {"status": "success", "reply": "Playing Shape of You", "intent": "play_music", ...},
        ]
    }
}
```

Status aggregation rules for chains:
- All results `success` → `"success"`
- All results `error`/`skipped` and 0 successes → `"error"`
- Mixed → `"partial"`

---

### Data Flow Diagram (Full System)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Input Sources                              │
│                                                                      │
│  Microphone ──► voice/stt.py ──► voice_adapter.py ──┐              │
│                                                       │              │
│  HTTP Client ──► api/routes.py ──────────────────────┤              │
└───────────────────────────────────────────────────────┼──────────────┘
                                                        │
                                                        ▼
                              ┌─────────────────────────────────────┐
                              │   core/command_executor.py          │
                              │   execute_command(text)             │
                              │                                      │
                              │  split_commands(text)               │
                              │    ├─ single → execute_single()     │
                              │    └─ chain  → execute_chain()      │
                              │                    └─ execute_single() × N
                              │                                      │
                              │   core/intent_parser.py             │
                              │   parse_intent(text)                │
                              │           │                          │
                              │           ▼                          │
                              │   HANDLERS[intent] → handler()      │
                              └─────────────┬───────────────────────┘
                                            │
              ┌─────────────────────────────┼────────────────────────┐
              │                             │                         │
              ▼                             ▼                         ▼
    handlers/task_handler         handlers/chat_handler     handlers/system_handler
    handlers/browser_handler      (Ollama LLM fallback)     handlers/app_handler
    handlers/media_handler                 │                 handlers/...
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
                              ┌───────────────────────────────────────────────┐
                              │         ResponseDict / Chain_Response         │
                              │  {"status", "reply", "intent", "payload"}    │
                              └────────────────┬──────────────────────────────┘
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

**Tests (all):**
```cmd
python -m pytest tests/ -v
```

**Tests (command chaining only):**
```cmd
python -m pytest tests/test_command_chain.py -v
```
