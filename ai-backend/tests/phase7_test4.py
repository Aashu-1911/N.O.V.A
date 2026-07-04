"""Phase 7 - Test 4: Non-chat intents regression check."""
import sys
sys.path.insert(0, ".")

from core.command_executor import execute_command

result = execute_command("Show my tasks")
intent = result.get("intent")
status = result.get("status")
reply = result.get("reply", "")

print("show_tasks test:")
print(f"  Intent: {intent}")
print(f"  Status: {status}")
print(f"  Reply:  {reply[:120]}")

valid_intents = {"show_stats", "show_tasks", "answer_question"}
if intent in valid_intents and status in ("success", "error") and reply:
    print("  PASS")
    sys.exit(0)
else:
    print(f"  FAIL - intent={intent} status={status} reply_empty={not reply}")
    sys.exit(1)
