"""
command_chain.py — Command splitting, dependency detection, and sequential
execution for chained user commands.

This module is responsible for:
  - Splitting a compound user utterance into individual sub-commands
    (split_commands), while protecting quoted text and URLs from being
    broken on connector keywords.
  - Classifying each sub-command as dependent or independent relative to
    its predecessor (_is_dependent).
  - Updating the shared ExecutionContext after each sub-command executes
    (_update_context).
  - Executing a list of sub-commands sequentially, respecting dependency
    rules, and assembling a Chain_Response (execute_chain).

IMPORT CONSTRAINT: This module MUST NOT import from core.command_executor.
The execution function is injected as a parameter at call time to avoid
circular imports. Only the standard library, core.execution_context, and
core.intent_parser may be imported.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from core.execution_context import ExecutionContext
from core.intent_parser import parse_intent


# ---------------------------------------------------------------------------
# Connector pattern (case-insensitive); order matters — longer phrases first
# ---------------------------------------------------------------------------
_CONNECTOR_PATTERN = re.compile(
    r"\s*\b(?:after\s+that|and|then|also)\b\s*|\s*,\s*",
    re.IGNORECASE,
)

# Patterns for regions that must be protected from splitting
_QUOTED_PATTERN = re.compile(r'(?:"[^"]*"|\'[^\']*\')')
_URL_PATTERN = re.compile(r'(?:https?://\S+|www\.\S+)', re.IGNORECASE)

# Word-boundary pronoun/reference tokens that signal a dependent command.
# Multi-word tokens ("this app", "this window") are checked with simple
# substring matching because they cannot match partial words anyway.
_PRONOUN_WB_PATTERNS = [
    re.compile(r'\bit\b', re.IGNORECASE),
    re.compile(r'\bthat\b', re.IGNORECASE),
    re.compile(r'\bthere\b', re.IGNORECASE),
]
_PRONOUN_SUBSTRING_TOKENS = ["this app", "this window", "this project", "this file", "this folder"]

# Intent values that qualify as media intents (for media-after-app check)
_MEDIA_INTENTS = {"media_control", "play_music"}

# Window intents that update last_window / last_window_handle on success
_WINDOW_INTENTS = {
    "focus_window",
    "maximize_window",
    "minimize_window",
    "restore_window",
    "get_active_window",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def split_commands(text: str) -> list[str]:
    """Split *text* into sub-commands at unprotected connector keywords.

    Protected regions (quoted strings and URLs) are never split even when
    they contain connector words. Returns a list of one element — the
    original text — when no unprotected connector is found or when an
    internal error occurs.

    Parameters
    ----------
    text:
        The raw user utterance.

    Returns
    -------
    list[str]
        One or more trimmed, non-empty sub-command strings.
    """
    try:
        if not text or not text.strip():
            return [text]

        # ---- Step 1: build protection mask ---------------------------------
        # We replace each protected region with a same-length run of a neutral
        # character ('X') so that the connector-splitting regex cannot match
        # inside those regions, yet all character positions stay aligned.

        protected_ranges: list[tuple[int, int]] = []
        for pattern in (_QUOTED_PATTERN, _URL_PATTERN):
            for m in pattern.finditer(text):
                protected_ranges.append((m.start(), m.end()))

        # Build the masked string
        if protected_ranges:
            chars = list(text)
            for start, end in protected_ranges:
                for i in range(start, end):
                    chars[i] = 'X'
            masked = "".join(chars)
        else:
            masked = text

        # ---- Step 2: find connector spans in the masked string -------------
        split_positions: list[tuple[int, int]] = []
        for m in _CONNECTOR_PATTERN.finditer(masked):
            split_positions.append((m.start(), m.end()))

        if not split_positions:
            return [text]

        # ---- Step 3: extract sub-commands from the *original* string -------
        segments: list[str] = []
        prev_end = 0
        for conn_start, conn_end in split_positions:
            segment = text[prev_end:conn_start]
            stripped = segment.strip()
            if stripped:
                segments.append(stripped)
            prev_end = conn_end

        # Tail after the last connector
        tail = text[prev_end:].strip()
        if tail:
            segments.append(tail)

        # If somehow nothing survived, fall back to the original
        if not segments:
            return [text]

        return segments

    except Exception:
        # Any internal regex or processing failure → treat as single command
        return [text]


def _is_dependent(cmd: str, prev_intent: Optional[str]) -> bool:
    """Return True when *cmd* is a Dependent_Command relative to its predecessor.

    Two conditions can make a sub-command dependent:

    1. **Pronoun-token**: the lowercased sub-command contains a reference
       pronoun or phrase ("it", "that", "there", "this app", "this window").
       Word-boundary checks are used for "it" and "that" to avoid false
       positives on words like "twitter" or "something".

    2. **Media-after-app**: the sub-command's intent is ``media_control`` or
       ``play_music`` AND the previous sub-command's intent was
       ``open_application``.  Intent is resolved lazily — ``parse_intent()``
       is only called when the pronoun check fails.

    Parameters
    ----------
    cmd:
        The sub-command text to classify.
    prev_intent:
        The ``last_intent`` value from the current ``ExecutionContext``, or
        ``None`` if this is the first command in the chain.

    Returns
    -------
    bool
    """
    lower_cmd = cmd.lower()

    # ---- Condition 1: pronoun / reference token (word-boundary) ------------
    for pattern in _PRONOUN_WB_PATTERNS:
        if pattern.search(lower_cmd):
            return True

    for token in _PRONOUN_SUBSTRING_TOKENS:
        if token in lower_cmd:
            return True

    # ---- Condition 2: media intent following open_application (lazy) -------
    if prev_intent == "open_application":
        try:
            intent_result = parse_intent(cmd)
            if intent_result.get("intent") in _MEDIA_INTENTS:
                return True
        except Exception:
            pass  # If intent parsing fails, default to independent

    return False


def _update_context(ec: ExecutionContext, cmd: str, result: dict) -> None:
    """Update *ec* fields based on the outcome of a completed sub-command.

    Rules (applied in order):
    - ``last_command`` is always set to *cmd*.
    - ``last_intent`` is set to ``result["intent"]`` unless the result's
      status is ``"skipped"`` (skipped commands are not considered to have
      "run", so the previous intent is preserved).
    - When status is ``"success"`` and intent is ``"open_application"``,
      ``last_app`` and ``last_window`` are set to ``result["payload"]["app_name"]``.
    - When status is ``"success"`` and intent is ``"open_website"``,
      ``last_website`` is set to ``result["payload"]["url"]``.

    ``parse_intent()`` is NOT called here; all information is read from
    *result* which was already produced by the handler pipeline.

    Parameters
    ----------
    ec:
        The mutable ``ExecutionContext`` to update in place.
    cmd:
        The raw sub-command text that was just executed.
    result:
        The ``ResponseDict`` (or skipped/error dict) returned for *cmd*.
    """
    ec.last_command = cmd

    status = result.get("status")
    intent = result.get("intent")

    if status != "skipped":
        ec.last_intent = intent

    if status == "success":
        payload = result.get("payload") or {}
        if intent == "open_application":
            app_name = payload.get("app_name")
            ec.last_app = app_name
            ec.last_window = app_name  # placeholder until real window-title lookup
        elif intent == "open_website":
            ec.last_website = payload.get("url")
        elif intent in _WINDOW_INTENTS:
            ec.last_window = payload.get("window_title")
            ec.last_window_handle = payload.get("window_handle")


def execute_chain(
    commands: list[str],
    execute_fn: Callable[[str, dict], dict],
) -> dict:
    """Execute *commands* sequentially, respecting dependency rules.

    Accepts the execution function as a parameter so that this module has
    zero imports from ``core.command_executor`` (avoiding circular imports).

    Parameters
    ----------
    commands:
        Ordered list of sub-command strings to execute.
    execute_fn:
        Callable with signature ``(command: str, context: dict) -> dict``.
        Called for every non-skipped sub-command.  Must return a
        ``ResponseDict``-shaped dict with at least ``"status"``, ``"reply"``,
        and ``"intent"`` keys.

    Returns
    -------
    dict
        A ``Chain_Response`` with the following top-level keys:

        - ``"status"``  — ``"success"`` | ``"partial"`` | ``"error"``
        - ``"reply"``   — natural-language summary joined with " and "
        - ``"intent"``  — always ``"chain"``
        - ``"payload"`` — ``{"executed_commands": [...], "results": [...]}``
    """
    ec = ExecutionContext()
    results: list[dict] = []
    prev_cmd: Optional[str] = None

    for i, cmd in enumerate(commands):
        dep = _is_dependent(cmd, ec.last_intent)

        # Determine whether this is a strict pronoun/reference dependency
        is_strict_dep = False
        lower_cmd = cmd.lower()
        for pattern in _PRONOUN_WB_PATTERNS:
            if pattern.search(lower_cmd):
                is_strict_dep = True
                break
        if not is_strict_dep:
            for token in _PRONOUN_SUBSTRING_TOKENS:
                if token in lower_cmd:
                    is_strict_dep = True
                    break

        # Determine whether the immediately preceding result was an error
        prev_result = results[i - 1] if i > 0 else None
        prereq_failed = (
            is_strict_dep
            and prev_result is not None
            and prev_result.get("status") == "error"
        )

        if prereq_failed:
            # Skip this dependent command and record a human-readable entry
            skip_reply = (
                f"Could not complete '{prev_cmd}', so '{cmd}' was skipped."
            )
            result: dict = {
                "status": "skipped",
                "reply": skip_reply,
                "intent": "skipped",
            }
            results.append(result)
            # Only last_command is updated for skipped entries
            ec.last_command = cmd
            prev_cmd = cmd
            continue

        # Build a shallow context snapshot for execute_fn
        sub_ctx: dict = dict(ec.__dict__)
        sub_ctx["raw_command"] = cmd

        # If previous command opened an application or website, wait a brief moment for it to load/be ready
        if i > 0 and ec.last_intent in {"open_application", "open_website"}:
            import sys
            if not any(m in sys.modules for m in ("pytest", "unittest", "_pytest")):
                import time
                time.sleep(1.5)

        try:
            result = execute_fn(cmd, sub_ctx)
        except Exception as exc:
            result = {
                "status": "error",
                "reply": f"Unexpected error executing '{cmd}': {exc}",
                "intent": "unknown",
            }

        results.append(result)
        _update_context(ec, cmd, result)
        prev_cmd = cmd

    # ---- Status aggregation -------------------------------------------------
    successes = sum(1 for r in results if r.get("status") == "success")
    errors = sum(1 for r in results if r.get("status") == "error")
    skipped = sum(1 for r in results if r.get("status") == "skipped")

    if errors == 0 and skipped == 0:
        chain_status = "success"
    elif successes == 0:
        chain_status = "error"
    else:
        chain_status = "partial"

    # ---- Reply combining ----------------------------------------------------
    cleaned_replies = []
    for r in results:
        reply = r.get("reply")
        if reply:
            cleaned = _clean_list_markers(reply)
            if cleaned:
                cleaned_replies.append(cleaned)
    combined_reply = " and ".join(cleaned_replies)

    return {
        "status": chain_status,
        "reply": combined_reply,
        "intent": "chain",
        "payload": {
            "executed_commands": commands,
            "results": results,
        },
    }


def _clean_list_markers(text: str) -> str:
    text = text.strip()
    if text in {"*", "-", "+", ""}:
        return ""
    # Strip leading bullet/numbered list patterns
    text = re.sub(r'^\s*[-*+]\s+', '', text)
    text = re.sub(r'^\s*\d+\.\s+', '', text)
    # Strip newline-prefixed bullet/numbered list patterns and join with space
    text = re.sub(r'\n\s*[-*+]\s+', ' ', text)
    text = re.sub(r'\n\s*\d+\.\s+', ' ', text)
    # Replace remaining newlines with spaces
    text = text.replace('\n', ' ')
    return text.strip()
