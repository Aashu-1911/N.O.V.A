"""
Unit tests for command chaining functionality.

Covers:
  - Task 5.1: split_commands
  - Task 5.2: _is_dependent, _update_context
  - Task 5.3: execute_chain, execute_command integration
"""

import sys
import os
import re
import unittest
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure the ai-backend root is on sys.path so core.* imports work when
# running pytest from inside tests/ or from the project root.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.command_chain import split_commands, _is_dependent, _update_context, execute_chain
from core.execution_context import ExecutionContext


# =============================================================================
# Task 5.1 — split_commands
# =============================================================================

class TestSplitCommands:

    def test_split_single_command(self):
        """A plain single command must be returned as a one-element list."""
        result = split_commands("add task to learn Docker")
        assert result == ["add task to learn Docker"]

    def test_split_two_commands_and(self):
        """' and ' connector must produce two sub-commands."""
        result = split_commands("open chrome and search openai")
        assert len(result) == 2

    def test_split_two_commands_then(self):
        """' then ' connector must produce two sub-commands."""
        result = split_commands("open vs code then maximize it")
        assert len(result) == 2

    def test_split_comma(self):
        """Comma connector must produce two sub-commands."""
        result = split_commands("mute volume, open telegram")
        assert len(result) == 2

    def test_split_three_commands(self):
        """Multiple ' and ' connectors must produce three sub-commands."""
        result = split_commands("open chrome and open telegram and mute volume")
        assert len(result) == 3

    def test_split_protected_url(self):
        """A URL containing '&' in its query string must not be split."""
        result = split_commands("open https://example.com?a=1&b=2")
        assert len(result) == 1

    def test_split_protected_quotes(self):
        """' and ' inside double-quoted text must not cause a split."""
        result = split_commands('search for "rock and roll"')
        assert len(result) == 1

    def test_split_discards_empty(self):
        """Trailing connector must not produce an empty/whitespace segment."""
        result = split_commands("open chrome and")
        # Every element must be non-empty after stripping whitespace
        assert all(seg.strip() for seg in result)


# =============================================================================
# Task 5.2 — _is_dependent, _update_context
# =============================================================================

class TestIsDependent:

    def test_dependency_pronoun_it(self):
        """Pronoun 'it' must make the command dependent."""
        assert _is_dependent("maximize it", None) is True

    def test_dependency_pronoun_this_app(self):
        """Phrase 'this app' must make the command dependent."""
        assert _is_dependent("close this app", None) is True

    def test_dependency_media_after_app(self):
        """Media intent following open_application must be detected as dependent."""
        with patch("core.command_chain.parse_intent",
                   return_value={"intent": "play_music", "entities": {}}):
            result = _is_dependent("play shape of you", "open_application")
        assert result is True

    def test_dependency_independent(self):
        """A command with no pronoun and non-media intent must be independent."""
        assert _is_dependent("lock pc", "add_task") is False


class TestUpdateContext:

    def test_update_context_last_command(self):
        """last_command is always updated to the cmd argument."""
        ec = ExecutionContext()
        _update_context(ec, "open chrome", {"status": "success", "intent": "open_application",
                                             "payload": {"app_name": "chrome"}})
        assert ec.last_command == "open chrome"

    def test_update_context_last_app(self):
        """Successful open_application sets last_app and last_window."""
        ec = ExecutionContext()
        result = {
            "status": "success",
            "intent": "open_application",
            "payload": {"app_name": "spotify"},
        }
        _update_context(ec, "open spotify", result)
        assert ec.last_app == "spotify"
        assert ec.last_window == "spotify"

    def test_update_context_last_website(self):
        """Successful open_website sets last_website."""
        ec = ExecutionContext()
        result = {
            "status": "success",
            "intent": "open_website",
            "payload": {"url": "https://google.com"},
        }
        _update_context(ec, "open google", result)
        assert ec.last_website == "https://google.com"

    def test_update_context_skipped_preserves_intent(self):
        """A skipped result must NOT overwrite last_intent."""
        ec = ExecutionContext()
        ec.last_intent = "open_application"  # set a prior intent

        skipped_result = {
            "status": "skipped",
            "intent": "skipped",
            "reply": "skipped because prior failed",
        }
        _update_context(ec, "maximize it", skipped_result)

        # last_command updated, but last_intent stays as before
        assert ec.last_command == "maximize it"
        assert ec.last_intent == "open_application"


# =============================================================================
# Task 5.3 — execute_chain and execute_command integration
# =============================================================================

class TestExecuteChain:

    # ------------------------------------------------------------------
    # Dependency / skip behaviour
    # ------------------------------------------------------------------

    def test_dependency_skipped_on_failure(self):
        """Dependent command must be skipped when its prerequisite failed."""
        first_result = {
            "status": "error",
            "reply": "failed",
            "intent": "open_application",
        }
        execute_fn = MagicMock(return_value=first_result)

        commands = ["open chrome", "maximize it"]
        response = execute_chain(commands, execute_fn)

        results = response["payload"]["results"]
        assert results[1]["status"] == "skipped"
        # execute_fn must have been called only once (for the first command)
        execute_fn.assert_called_once()

    def test_dependency_executes_on_success(self):
        """Dependent command must execute normally when its prerequisite succeeded."""
        first_result = {
            "status": "success",
            "reply": "opened",
            "intent": "open_application",
            "payload": {"app_name": "spotify"},
        }
        execute_fn = MagicMock(return_value=first_result)

        commands = ["open spotify", "maximize it"]
        execute_chain(commands, execute_fn)

        assert execute_fn.call_count == 2

    def test_independent_continues_on_failure(self):
        """An independent command must still execute even when the prior one failed."""
        first_result = {"status": "error", "reply": "err", "intent": "open_application"}
        execute_fn = MagicMock(return_value=first_result)

        commands = ["open chrome", "open telegram"]
        execute_chain(commands, execute_fn)

        assert execute_fn.call_count == 2

    def test_three_commands_all_independent(self):
        """Three independent commands: all executed, none skipped."""
        success_result = {"status": "success", "reply": "done", "intent": "test"}
        execute_fn = MagicMock(return_value=success_result)

        commands = ["lock pc", "open telegram", "mute volume"]
        response = execute_chain(commands, execute_fn)

        results = response["payload"]["results"]
        for r in results:
            assert r["status"] in ("success", "error")
            assert r["status"] != "skipped"
        assert execute_fn.call_count == 3

    # ------------------------------------------------------------------
    # Status aggregation
    # ------------------------------------------------------------------

    def test_status_all_success(self):
        """All successes → chain status == 'success'."""
        execute_fn = MagicMock(return_value={"status": "success", "reply": "ok", "intent": "test"})
        response = execute_chain(["lock pc", "mute volume"], execute_fn)
        assert response["status"] == "success"

    def test_status_all_fail(self):
        """All errors → chain status == 'error'."""
        execute_fn = MagicMock(return_value={"status": "error", "reply": "err", "intent": "test"})
        response = execute_chain(["lock pc", "mute volume"], execute_fn)
        assert response["status"] == "error"

    def test_status_mixed(self):
        """First succeeds, second fails → chain status == 'partial'."""
        results_seq = iter([
            {"status": "success", "reply": "ok", "intent": "test"},
            {"status": "error",   "reply": "err", "intent": "test"},
        ])
        execute_fn = MagicMock(side_effect=results_seq)
        response = execute_chain(["lock pc", "mute volume"], execute_fn)
        assert response["status"] == "partial"

    # ------------------------------------------------------------------
    # Response shape
    # ------------------------------------------------------------------

    def test_chain_response_intent(self):
        """Chain response must always have intent == 'chain'."""
        execute_fn = MagicMock(return_value={"status": "success", "reply": "ok", "intent": "test"})
        response = execute_chain(["lock pc", "mute volume"], execute_fn)
        assert response["intent"] == "chain"

    def test_chain_response_payload_lengths(self):
        """executed_commands and results must have the same length as the input list."""
        commands = ["lock pc", "open telegram", "mute volume"]
        execute_fn = MagicMock(return_value={"status": "success", "reply": "ok", "intent": "test"})
        response = execute_chain(commands, execute_fn)
        payload = response["payload"]
        assert len(payload["executed_commands"]) == len(commands)
        assert len(payload["results"]) == len(commands)


# =============================================================================
# Task 5.3 — execute_command integration (single-command regression)
# =============================================================================

class TestExecuteCommandIntegration:

    def test_single_command_regression(self):
        """A single command must bypass execute_chain and return a non-chain response."""
        fake_response = {
            "status": "success",
            "reply": "added",
            "intent": "add_task",
            "payload": {},
        }
        import core.command_executor as _ce
        with patch.object(_ce, "execute_single", return_value=fake_response):
            response = _ce.execute_command("add task to learn Docker")

        # Must NOT be a chain response
        assert response.get("intent") != "chain"
        assert "executed_commands" not in response.get("payload", {})


# =============================================================================
# Helper — strip all connector tokens from arbitrary text
# =============================================================================

def _remove_connectors(text: str) -> str:
    """Remove all unprotected connector keywords from *text*.

    Uses the same connector vocabulary and boundary rules recognised by
    split_commands so that the cleaned text is guaranteed to contain no
    splitting triggers. Mirrors the word-boundary + zero-or-more-spaces
    spacing used by _CONNECTOR_PATTERN in command_chain.py.
    """
    return re.sub(
        r'(?i)\s*\band\b\s*|\s*\bthen\b\s*|\s*\bafter\s+that\b\s*|\s*\balso\b\s*|\s*,\s*',
        '',
        text,
    )


# =============================================================================
# Task 5.4 — Property 1: Connector-guarded splitting
# =============================================================================

class TestProperty1ConnectorGuardedSplitting:

    @given(text=st.text(min_size=1).filter(lambda s: s.strip()))
    @settings(max_examples=100)
    def test_property_1_no_connector_returns_single(self, text):
        """Feature: command-chaining, Property 1: no-connector input returns single element.
        Validates Requirements 1.1, 1.2, 1.3, 1.4, 1.5
        """
        clean = _remove_connectors(text)
        assume(bool(clean.strip()))
        result = split_commands(clean)
        assert len(result) == 1
        assert all(s.strip() for s in result)


# =============================================================================
# Task 5.5 — Property 2: Chain response shape invariant
# =============================================================================

class TestProperty2ChainResponseShape:

    @given(commands=st.lists(st.text(min_size=1), min_size=2, max_size=5))
    @settings(max_examples=100)
    def test_property_2_chain_response_shape(self, commands):
        """Feature: command-chaining, Property 2: chain response shape invariant"""
        # Validates: Requirements 2.3, 2.4, 10.1, 10.2, 10.3, 10.4
        execute_fn = lambda cmd, ctx: {"status": "success", "reply": "ok", "intent": "test"}
        response = execute_chain(commands, execute_fn)

        assert response["intent"] == "chain"
        assert len(response["payload"]["executed_commands"]) == len(commands)
        assert len(response["payload"]["results"]) == len(commands)
        for result in response["payload"]["results"]:
            assert "status" in result
            assert "reply" in result


# =============================================================================
# Task 5.6 — Property 3: ExecutionContext field updates
# =============================================================================

class TestProperty3ExecutionContextFieldUpdates:

    @given(app_name=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))).filter(str.strip))
    @settings(max_examples=100)
    def test_property_3_last_app_updated(self, app_name):
        """Feature: command-chaining, Property 3: last_app and last_window updated after open_application success. Validates Requirements 3.2, 3.4"""
        ec = ExecutionContext()
        result = {"status": "success", "intent": "open_application", "payload": {"app_name": app_name}}
        _update_context(ec, "open " + app_name, result)
        assert ec.last_app == app_name
        assert ec.last_window == app_name

    @given(url=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Po"))).filter(str.strip))
    @settings(max_examples=100)
    def test_property_3_last_website_updated(self, url):
        """Feature: command-chaining, Property 3: last_website updated after open_website success. Validates Requirements 3.3, 3.4"""
        ec = ExecutionContext()
        result = {"status": "success", "intent": "open_website", "payload": {"url": url}}
        _update_context(ec, "open " + url, result)
        assert ec.last_website == url


# =============================================================================
# Task 5.7 — Property 4: Dependency skip iff prerequisite failed
# =============================================================================

@given(
    n=st.integers(min_value=2, max_value=5),
    fail_idx=st.integers(min_value=0, max_value=4).filter(lambda i: i < 5),
)
@settings(max_examples=100)
def test_property_5_independent_commands_always_execute(n, fail_idx):
    """Feature: command-chaining, Property 5: independent commands always execute.

    **Validates: Requirements 4.4, 5.1, 5.2**

    All commands in the chain are non-pronoun (independent). Even when one
    command fails, the rest must still be executed — none should be 'skipped'.
    """
    # Build n non-pronoun commands — no "it", "that", "there", "this app", "this window"
    commands = [f"lock pc number {i}" for i in range(n)]

    call_count = [0]

    def side_effect(cmd, ctx):
        idx = call_count[0]
        call_count[0] += 1
        if idx == fail_idx % n:
            return {"status": "error", "reply": "error", "intent": "test"}
        return {"status": "success", "reply": "done", "intent": "test"}

    execute_fn = MagicMock(side_effect=side_effect)

    response = execute_chain(commands, execute_fn)
    results = response["payload"]["results"]

    assert len(results) == n, f"Expected {n} results, got {len(results)}"
    for i, result in enumerate(results):
        assert result["status"] in ("success", "error"), (
            f"results[{i}] has status '{result['status']}' — expected 'success' or 'error', never 'skipped'"
        )


@given(prereq_status=st.sampled_from(["success", "error"]))
@settings(max_examples=100)
def test_property_4_dependent_skipped_iff_prereq_failed(prereq_status):
    """Feature: command-chaining, Property 4: dependent command is skipped iff prerequisite failed.

    **Validates: Requirements 4.3, 4.4a**
    """
    # Build a MagicMock that returns the prereq status on the first call and
    # a success result on the second call (when prereq succeeds).
    execute_fn = MagicMock(side_effect=[
        {"status": prereq_status, "reply": "ok", "intent": "open_application"},
        {"status": "success", "reply": "ok", "intent": "some_intent"},
    ])

    commands = ["open chrome", "maximize it"]
    response = execute_chain(commands, execute_fn)
    results = response["payload"]["results"]

    if prereq_status == "error":
        # Dependent command must be skipped; execute_fn called exactly once
        assert results[1]["status"] == "skipped", (
            f"Expected results[1] to be 'skipped' when prereq failed, got '{results[1]['status']}'"
        )
        execute_fn.assert_called_once()
    else:
        # prereq_status == "success": dependent command must execute
        assert execute_fn.call_count == 2, (
            f"Expected execute_fn to be called twice when prereq succeeded, got {execute_fn.call_count}"
        )
        assert results[1]["status"] in ("success", "error"), (
            f"Expected results[1] status to be 'success' or 'error', got '{results[1]['status']}'"
        )
        assert results[1]["status"] != "skipped", (
            "results[1] must never be 'skipped' when prereq succeeded"
        )


# =============================================================================
# Task 5.9 — Property 6: Status aggregation formula
# =============================================================================

class TestProperty6StatusAggregation:

    @given(
        successes=st.integers(min_value=0, max_value=5),
        errors=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=100)
    def test_property_6_status_aggregation_formula(self, successes, errors):
        """Feature: command-chaining, Property 6: status aggregation formula.

        **Validates: Requirements 5.3**

        For any mix of successes and errors (with at least 2 commands, all
        independent non-pronouns, so skipped == 0):
          - chain_status == "success"  when errors == 0
          - chain_status == "error"    when successes == 0
          - chain_status == "partial"  otherwise (successes > 0 and errors > 0)
        """
        assume(successes + errors >= 2)

        # Build non-pronoun commands — no "it", "that", "there", etc.
        commands = [f"lock pc {i}" for i in range(successes + errors)]

        # Build side_effect list: successes first, then errors
        side_effects = (
            [{"status": "success", "reply": "ok", "intent": "test"}] * successes
            + [{"status": "error", "reply": "err", "intent": "test"}] * errors
        )

        execute_fn = MagicMock(side_effect=side_effects)
        response = execute_chain(commands, execute_fn)
        chain_status = response["status"]

        if errors == 0:
            assert chain_status == "success", (
                f"Expected 'success' when errors=0, successes={successes}, "
                f"got '{chain_status}'"
            )
        elif successes == 0:
            assert chain_status == "error", (
                f"Expected 'error' when successes=0, errors={errors}, "
                f"got '{chain_status}'"
            )
        else:
            assert chain_status == "partial", (
                f"Expected 'partial' when successes={successes}, errors={errors}, "
                f"got '{chain_status}'"
            )


# =============================================================================
# Task 5.10 — Property 7: Natural reply joining
# =============================================================================

class TestProperty7NaturalReplyJoining:

    @given(replies=st.lists(st.text(min_size=1).filter(str.strip), min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_property_7_natural_reply_joining(self, replies):
        """Feature: command-chaining, Property 7: natural reply joining.

        **Validates: Requirements 6.1, 6.2, 6.3**

        The combined reply must be a plain string with no bullet/numbered list
        markers — neither leading markers (- , * , 1.) nor embedded
        newline-prefixed list items (\n- , \n* ).
        """
        # Build an iterator-backed execute_fn that returns each reply in sequence
        results_iter = iter([
            {"status": "success", "reply": r, "intent": "test"}
            for r in replies
        ])
        execute_fn = lambda cmd, ctx: next(results_iter)

        # Use non-pronoun commands so no command is skipped
        commands = [f"lock pc {i}" for i in range(len(replies))]

        response = execute_chain(commands, execute_fn)
        combined = response["reply"]

        # The combined reply must be a plain string
        assert isinstance(combined, str)

        # No leading bullet markers (- item, * item)
        assert re.search(r'(?m)^\s*[-*]\s', combined) is None, (
            f"Combined reply contains bullet list marker: {combined!r}"
        )

        # No leading numbered list markers (1. item)
        assert re.search(r'(?m)^\s*\d+\.\s', combined) is None, (
            f"Combined reply contains numbered list marker: {combined!r}"
        )

        # No embedded newline-prefixed list items
        assert '\n- ' not in combined, (
            f"Combined reply contains embedded '\\n- ': {combined!r}"
        )
        assert '\n* ' not in combined, (
            f"Combined reply contains embedded '\\n* ': {combined!r}"
        )


# =============================================================================
# Task 5.11 — Property 8: Single-command passthrough
# =============================================================================

class TestProperty8SingleCommandPassthrough:

    @given(
        cmd=st.text(min_size=1)
            .filter(lambda s: len(split_commands(s)) == 1)
            .filter(str.strip)
    )
    @settings(max_examples=100)
    def test_property_8_single_command_passthrough(self, cmd):
        """Feature: command-chaining, Property 8: single-command passthrough.

        Validates Requirements 7.3, 9.4

        For any input that split_commands() classifies as a single command,
        execute_command() must return a standard ResponseDict with:
          - intent != "chain"
          - no "executed_commands" key inside payload
        """
        fake_response = {
            "status": "success",
            "reply": "done",
            "intent": "add_task",
            "payload": {},
        }
        import core.command_executor as _ce
        with patch.object(_ce, "execute_single", return_value=fake_response):
            response = _ce.execute_command(cmd)

        assert response.get("intent") != "chain", (
            f"Expected intent != 'chain' for single command {cmd!r}, "
            f"got intent={response.get('intent')!r}"
        )
        assert "executed_commands" not in response.get("payload", {}), (
            f"'executed_commands' must not appear in payload for a single command {cmd!r}"
        )
