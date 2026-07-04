"""Phase 7 - Test 2: General chat handles connection error gracefully."""
import sys
sys.path.insert(0, ".")

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

    print(f"Query: {query}")
    print(f"  Intent: {intent}")
    print(f"  Status: {status}")
    print(f"  Reply:  {reply[:120]}")

    if status not in ("success", "error"):
        print(f"  FAIL - unexpected status: {status}")
        all_passed = False
    elif not reply:
        print(f"  FAIL - reply is empty")
        all_passed = False
    else:
        if ollama_running is None:
            ollama_running = status == "success"
        print(f"  PASS")
    print()

print(f"Ollama running: {ollama_running}")
print(f"RESULT: {'PASS' if all_passed else 'FAIL'}")
sys.exit(0 if all_passed else 1)
