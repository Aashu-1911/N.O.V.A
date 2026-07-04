# Migration Guide: Voice-API Separation Refactor

## Overview

This document describes the architectural refactor that separated voice processing
from command execution within the AI Assistant application.

### Why this refactor was done

Before the refactor, the code had a **circular dependency**:

- `voice/` imported from `core/command_executor` (to handle commands after transcription).
- `core/command_executor` imported from `voice/` (to call `speak()` after execution).

This made the codebase fragile — you couldn't import either module in isolation, adding a
new interface (GUI, CLI, mobile) would require modifying core business logic, and unit
testing individual components was extremely difficult.

**Goals of the refactor:**

1. Eliminate the circular dependency permanently.
2. Make `command_executor` interface-agnostic: it returns a dict and never calls `speak()`.
3. Establish a clean three-layer architecture (Input Adapters → Core → Output Adapters).
4. Enable future interfaces (GUI, CLI, mobile) without touching core logic.

---

## Before vs After

| Aspect | Before | After |
|---|---|---|
| Dependency direction | `voice ↔ command_executor` (circular) | `voice_adapter → voice` and `voice_adapter → executor` (one-way) |
| Who calls `speak()` | `command_executor` (core business logic) | `voice_adapter` only (adapter layer) |
| Who calls `execute_command()` | `voice/` and `api/routes.py` | `voice_adapter` and `api/routes.py` |
| Handler location | Monolithic inside `command_executor.py` | Separate files in `handlers/` directory |
| Response format | Inconsistent manual dicts | Standardised via `core/response_builder` |
| Voice isolation | `voice/` depended on managers | `voice/` has zero business-logic imports |
| Adding a new interface | Required modifying `command_executor.py` | Add a new adapter file only |

---

## The 13-Phase Migration Strategy

Each phase ended with a `git commit` so the team could roll back to a known-good state
at any time. Phases were designed to be small enough to test manually in under five minutes.

### Phase 0 — Git Checkpoint (Baseline)

**Purpose:** Create a clean baseline before any changes.

**Commit:** `Baseline before voice-api separation refactor`

Record the commit hash. If the entire refactor needs to be abandoned, `git checkout <hash>`
returns the codebase to this exact state.

---

### Phase 1 — Command Executor Skeleton

**Purpose:** Build a thin routing layer with empty handler stubs, so the architecture
compiles and runs before any business logic is moved.

**Key decisions:**
- Created `core/command_executor_v2.py` (kept old file intact for reference).
- Used a simple `HANDLERS` dict (`{"intent": handler_func}`), not a class.
- Stubs returned `{"status": "success", "reply": "Handler not implemented yet"}`.
- No `response_builder` yet — manual dicts only.
- No manager imports yet.

**Commit:** `Phase 1: Command executor skeleton with handler stubs`

---

### Phase 2 — Migrate Task Handler

**Purpose:** Move the first and most critical handler (tasks) to verify the pattern works end-to-end.

**What was moved:** `handle_add_task`, `handle_show_tasks`, `handle_complete_task`, `handle_show_stats`

**Manual test:** "Add task to test migration", "Show my tasks", POST `/execute`

**Commit:** `Phase 2: Migrate task handler`

---

### Phase 3 — Migrate Browser Handler

**Purpose:** Second handler migration to confirm the pattern generalises.

**What was moved:** `handle_open_browser`, `handle_search_web`

**Manual test:** "Open browser", "Search Google for Python tutorials"

**Commit:** `Phase 3: Migrate browser handler`

---

### Phase 4 — Migrate App Handler

**Purpose:** App launching/closing handler migration.

**What was moved:** `handle_open_app`, `handle_close_app`

**Manual test:** "Open Telegram", "Close Telegram"

**Commit:** `Phase 4: Migrate app handler`

---

### Phase 5 — Migrate System Handler

**Purpose:** OS-level system commands migration.

**What was moved:** `handle_lock_pc`, `handle_screenshot`, `handle_volume_control`

**Manual test:** "Lock screen", "Take screenshot", "Mute", "Volume up"

**Commit:** `Phase 5: Migrate system handler`

---

### Phase 6 — Migrate Media Handler

**Purpose:** Media playback handler migration.

**What was moved:** `handle_play_music`, `handle_media_control`

**Manual test:** "Play music", "Pause", "Next track"

**Commit:** `Phase 6: Migrate media handler`

---

### Phase 7 — Migrate Chat Handler

**Purpose:** LLM / general-chat fallback handler migration.

**What was moved:** `handle_general_chat` (wraps Ollama streaming)

**Manual test:** "What time is it?", "Tell me a joke", POST `/execute` with "How are you?"

**Commit:** `Phase 7: Migrate chat handler`

---

### Phase 8 — Voice Adapter Integration

**Purpose:** Create `adapters/voice_adapter.py` as the single file that imports both
`voice/` and `core/command_executor`. Update `main.py` to register the callback.

**Key decisions:**
- `voice_command_callback` is a plain function registered via `on_command()`.
- `format_for_voice()` strips markdown before calling `speak()`.
- `main.py` no longer contains any direct voice command handling logic.

**Commit:** `Phase 8: Voice adapter integration`

**Critical:** Verified ALL voice commands still worked after this change.

---

### Phase 9 — API Refactor

**Purpose:** Update `api/routes.py` to use the new `execute_command` from `command_executor_v2`.

**Key decisions:**
- `/execute` now calls `execute_command()` and returns the dict directly.
- `/chat` kept as a backward-compatible wrapper.
- No voice imports anywhere in `api/routes.py`.

**Commit:** `Phase 9: API refactor to use new command executor`

---

### Phase 10 — Cleanup and Consolidation

**Purpose:** Remove the migration artefacts (`_v2` suffix, `_old` backup) and establish
the permanent file structure.

**Steps:**
- Renamed `command_executor_v2.py` → `command_executor.py`
- Extracted all handlers from the monolithic executor into `handlers/*.py`
- Simplified `voice/wake_word.py` to a plain substring-match function
- Cleaned up `voice/__init__.py` exports
- Verified: `command_executor.py` has **zero** `voice` imports
- Verified: `voice/` has **zero** `core/` imports
- Verified: `adapters/voice_adapter.py` is the **only** file importing both

**Commit:** `Phase 10: Cleanup, extract handlers, verify architecture`

---

### Phase 11 — Response Builder

**Purpose:** Replace manual response dicts with standardised helpers now that the
architecture was stable and all tests were passing.

**Created:** `core/response_builder.py` with `success()`, `error()`, `partial()`.

**Updated:** All handlers in `handlers/*.py` to use the helpers.

**Commit:** `Phase 11: Integrate response_builder across all handlers`

---

### Phase 12 — Automated Tests

**Purpose:** Add an automated test suite now that the architecture was stable enough
that tests wouldn't need constant rewriting.

**Tests added:**
- Unit tests for `core/response_builder.py`
- Integration tests for `adapters/voice_adapter.py` callback flow
- Integration tests for `api/routes.py` HTTP adapter

**Commit:** `Phase 12: Add automated test suite`

---

### Phase 13 — Documentation

**Purpose:** Write comprehensive documentation for the new architecture.

**Documents created/updated:**
- `voice/README.md` — architecture overview, public API, flow diagrams
- All handler modules — full Google-style docstrings with Args, Returns, Example
- `core/command_executor.py` — architecture position, dependency rules
- `adapters/voice_adapter.py` — integration point explanation
- This file (`MIGRATION_GUIDE.md`)

**Commit:** `Phase 13: Update documentation for new architecture`

---

## Git Checkpoint Strategy

### Why every phase ended with a commit

- **Instant rollback**: if a phase breaks something, `git checkout <previous-hash>` restores
  the last known-good state in seconds.
- **Isolation**: each commit is small and focused, making it easy to understand what changed
  and why via `git log`.
- **Progress tracking**: the commit history serves as a migration log showing exactly which
  phase introduced each change.

### How to view the phase history

```bash
git log --oneline
```

Example output:
```
a1b2c3d Phase 13: Update documentation for new architecture
9e8f7g6 Phase 12: Add automated test suite
5d4c3b2 Phase 11: Integrate response_builder across all handlers
...
0a1b2c3 Baseline before voice-api separation refactor
```

---

## Manual Testing Checklist

Run these commands after each phase to verify nothing broke. Stop immediately if any
command fails — fix it before continuing to the next phase.

### Voice commands

| Category | Test command |
|---|---|
| Tasks | "Add task to test migration" |
| Tasks | "Show my tasks" |
| Tasks | "Complete task test migration" |
| Browser | "Open browser" |
| Browser | "Search Google for Python tutorials" |
| App | "Open Telegram" |
| App | "Close Telegram" |
| App | "Open Notepad" |
| System | "Lock screen" |
| System | "Take screenshot" |
| System | "Mute" |
| System | "Unmute" |
| System | "Volume up" |
| Media | "Play music" |
| Media | "Pause" |
| Media | "Next track" |
| Chat | "What time is it?" |
| Chat | "Tell me a joke" |

### API commands (curl or Postman)

```bash
# Task operations
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" \
     -d '{"message": "Add task via API"}'

curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" \
     -d '{"message": "Show my tasks"}'

# Browser
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" \
     -d '{"message": "Open browser"}'

# System
curl -X POST http://localhost:8000/execute -H "Content-Type: application/json" \
     -d '{"message": "Take screenshot"}'

# Backward-compatible chat endpoint
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
     -d '{"message": "How are you?"}'
```

---

## Rollback Strategy

### Roll back to a specific phase

```bash
# List commits with their hashes
git log --oneline

# Check out a specific commit (detached HEAD — read-only view)
git checkout <commit-hash>

# Create a branch from that commit if you want to continue from there
git checkout -b recovery/<phase-name> <commit-hash>
```

### Roll back the entire refactor

```bash
# Find the baseline commit hash (the very first commit in git log --oneline)
git log --oneline | tail -1

# Hard reset to baseline (DESTRUCTIVE — discards all changes since then)
git reset --hard <baseline-hash>
```

> **Warning:** `git reset --hard` discards all uncommitted and unpushed changes
> permanently. Only use it if you are certain you want to abandon all refactor work.

---

## Key Architectural Decisions

### 1. Command executor skeleton before filling handlers

Building the routing layer first (Phase 1) with stubs meant the architecture compiled
and could be manually tested immediately. Filling in real logic came later one handler
at a time, making failures easy to localise.

### 2. Manual response dicts before response_builder

Using raw dicts (`{"status": "success", "reply": "..."}`) in Phases 1–10 meant the
architecture could be validated without depending on `response_builder`. Adding
`response_builder` in Phase 11 was a pure refactor with no behavioural change.

### 3. Voice before API

Voice is more fragile than the HTTP API (it involves audio hardware, threading, and
real-time transcription). Fixing voice first in Phase 8 ensured the hardest part worked
before touching the API in Phase 9.

### 4. No automated tests during the refactor

Writing automated tests during a structural refactor means constantly rewriting tests
as the structure changes. Tests were written in Phase 12 once the architecture was stable
and the public API was finalised.

### 5. Simple `HANDLERS` dict instead of a class

A plain `dict` mapping intent names to handler functions is transparent, easy to read,
easy to extend, and requires no inheritance or method dispatch boilerplate.

---

## Dependency Rules (must never be broken)

These rules are the permanent invariants that define the architecture:

```
voice/*
    MUST NOT import from:  core/, handlers/, managers/, services/, api/

core/command_executor.py
    MUST NOT import from:  voice/
    (No speak() calls, no audio, no TTS)

adapters/voice_adapter.py
    Is the ONLY file allowed to import from both voice/ and core/command_executor
    This is intentional — it is the adapter / integration point

api/routes.py
    MUST NOT import from:  voice/
    It only imports from:  core/command_executor, core/intent_parser, managers/
```

Violating any of these rules re-introduces circular dependencies or couples the core to
a specific interface, undoing the purpose of the refactor.

To verify the rules are not broken, run:

```bash
# Should print nothing (no voice imports in command_executor)
grep -r "from voice" ai-backend/core/

# Should print nothing (no core imports in voice module)
grep -r "from core" ai-backend/voice/
grep -r "import core" ai-backend/voice/

# Should print only voice_adapter.py (the only allowed crossing point)
grep -r "from voice" ai-backend/adapters/
```
