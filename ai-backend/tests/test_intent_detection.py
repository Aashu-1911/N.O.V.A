"""Quick test to verify intent detection for task commands"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.intent_parser import parse_intent

test_phrases = [
    "list my tasks",
    "get tasks", 
    "show tasks",
    "what are my tasks",
    "Show my tasks",
    "list all tasks"
]

print("Testing intent detection for task listing:")
print("-" * 50)
for phrase in test_phrases:
    result = parse_intent(phrase)
    print(f"{phrase:25} -> {result['intent']}")
