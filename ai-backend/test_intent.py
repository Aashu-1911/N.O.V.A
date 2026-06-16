from ollama_client import parse_intent

print(parse_intent("Add a task to learn Docker tomorrow"))
print(parse_intent("Complete task LocalPulse"))
print(parse_intent("Show my progress"))