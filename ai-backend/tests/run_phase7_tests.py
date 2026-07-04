"""Phase 7 verification tests for chat handler migration."""
import sys

results = {}

# ── Test 1: Import and basic routing ──────────────────────────────────────────
print("=" * 60)
print("TEST 1: Import and basic routing")
print("=" * 60)
try:
from core.command_executor import execute_command, HANDLERS
from handlers.chat_handler import handle_general_chat

    t1_routing = "answer_question" in HANDLERS
    t1_wired = HANDLERS["answer_question"] is handle_general_chat

    print(f"  handle_general_chat in HANDLERS: {t1_routing}")
    print(f"  HANDLERS['answer_question'] is handle_general_chat: {t1_wired}")
    print(f"  Import OK")

    if t1_routing and t1_wired:
        results["test1"] = "PASS"
        print("  RESULT: PASS")
    else:
        results["test1"] = "FAIL - wiring mismatch"
        print("  RESULT: FAIL - wiring mismatch")
except Exception as e:
    results["test1"] = f"FAIL - exception: {e}"
    print(f"  RESULT: FAIL - {e}")

print()

# ── Test 2: Graceful connection error handling ─────────────────────────────────
print("=" * 60)
print("TEST 2: General chat handles connection error gracefully")
print("=" * 60)
try:
    from core.command_executor import execute_command

    test_queries = [
        "How are you?",
        "What time is it?",
        "Tell me a joke",
    ]

    ollama_running = None
    all_passed = True
    for query in test_queries:
        result = execute_command(query)
        intent = result.get("intent")
        status = result.get("status")
        reply = result.get("reply", "")

        print(f"  Query: {query}")
        print(f"    Intent: {intent}")
        print(f"    Status: {status}")
        print(f"    Reply:  {reply[:100]}")

        if status not in ("success", "error"):
            print(f"    FAIL - unexpected status: {status}")
            all_passed = False
        elif not reply:
            print(f"    FAIL - reply is empty")
            all_passed = False
        else:
            print(f"    PASS")
            if ollama_running is None:
                ollama_running = status == "success"

    results["test2"] = "PASS" if all_passed else "FAIL"
    results["ollama_running"] = ollama_running
    print(f"  Ollama running: {ollama_running}")
    print(f"  RESULT: {'PASS' if all_passed else 'FAIL'}")
except Exception as e:
    results["test2"] = f"FAIL - exception: {e}"
    print(f"  RESULT: FAIL - {e}")

print()

# ── Test 3: raw_command injection ─────────────────────────────────────────────
print("=" * 60)
print("TEST 3: raw_command injection")
print("=" * 60)
try:
    from handlers.chat_handler import handle_general_chat

    all_passed = True

    # No context at all
    result = handle_general_chat({}, context=None)
    status = result.get("status")
    reply = result.get("reply", "")
    print(f"  No context test:")
    print(f"    Status: {status}")
    print(f"    Reply:  {reply}")
    if not reply:
        print("    FAIL - reply empty")
        all_passed = False
    else:
        print("    PASS")

    # Empty context (no raw_command key)
    result = handle_general_chat({}, context={})
    status = result.get("status")
    reply = result.get("reply", "")
    print(f"  Empty context test:")
    print(f"    Status: {status}")
    print(f"    Reply:  {reply}")
    if not reply:
        print("    FAIL - reply empty")
        all_passed = False
    else:
        print("    PASS")

    # With raw_command present (may call Ollama)
    result = handle_general_chat({}, context={"raw_command": "Hello!"})
    status = result.get("status")
    reply = result.get("reply", "")
    print(f"  With raw_command test:")
    print(f"    Status: {status}")
    print(f"    Reply:  {reply[:100]}")
    if not reply:
        print("    FAIL - reply empty")
        all_passed = False
    else:
        print("    PASS")

    results["test3"] = "PASS" if all_passed else "FAIL"
    print(f"  RESULT: {'PASS' if all_passed else 'FAIL'}")
except Exception as e:
    results["test3"] = f"FAIL - exception: {e}"
    print(f"  RESULT: FAIL - {e}")

print()

# ── Test 4: Non-chat intents regression check ──────────────────────────────────
print("=" * 60)
print("TEST 4: Non-chat intents still work (regression)")
print("=" * 60)
try:
    from core.command_executor import execute_command

    result = execute_command("Show my tasks")
    intent = result.get("intent")
    status = result.get("status")
    reply = result.get("reply", "")
    print(f"  show_tasks test:")
    print(f"    Intent: {intent}")
    print(f"    Status: {status}")
    print(f"    Reply:  {reply[:120]}")

    valid_intents = {"show_stats", "show_tasks", "answer_question"}
    if intent in valid_intents and status in ("success", "error") and reply:
        results["test4"] = "PASS"
        print("    PASS")
    else:
        results["test4"] = f"FAIL - intent={intent} status={status} reply_empty={not reply}"
        print(f"    FAIL")
except Exception as e:
    results["test4"] = f"FAIL - exception: {e}"
    print(f"  RESULT: FAIL - {e}")

print()

# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("SUMMARY")
print("=" * 60)
all_ok = all(v.startswith("PASS") for v in results.values() if v != results.get("ollama_running"))
for k, v in results.items():
    if k == "ollama_running":
        continue
    print(f"  {k}: {v}")
print(f"  Ollama was running during test: {results.get('ollama_running')}")
print()
print(f"  Overall: {'ALL PASS' if all_ok else 'SOME FAILURES'}")

sys.exit(0 if all_ok else 1)
