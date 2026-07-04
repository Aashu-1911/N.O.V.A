"""Phase 7 - Test 3: raw_command injection."""
import sys
sys.path.insert(0, ".")

from handlers.chat_handler import handle_general_chat

all_passed = True

# No context at all
result = handle_general_chat({}, context=None)
status = result.get("status")
reply = result.get("reply", "")
print("No context test:")
print(f"  Status: {status}")
print(f"  Reply:  {reply}")
if not reply:
    print("  FAIL - reply empty")
    all_passed = False
else:
    print("  PASS")

# Empty context (no raw_command key)
result = handle_general_chat({}, context={})
status = result.get("status")
reply = result.get("reply", "")
print("Empty context test:")
print(f"  Status: {status}")
print(f"  Reply:  {reply}")
if not reply:
    print("  FAIL - reply empty")
    all_passed = False
else:
    print("  PASS")

# With raw_command present (calls Ollama if running)
result = handle_general_chat({}, context={"raw_command": "Hello!"})
status = result.get("status")
reply = result.get("reply", "")
print("With raw_command test:")
print(f"  Status: {status}")
print(f"  Reply:  {reply[:120]}")
if not reply:
    print("  FAIL - reply empty")
    all_passed = False
else:
    print("  PASS")

print()
print(f"RESULT: {'PASS' if all_passed else 'FAIL'}")
sys.exit(0 if all_passed else 1)
