from intent_router import route_command
import time

command = "Remind me to call mom tomorrow"

start = time.time()

result = route_command(command)

print("\nRESULT:")
print(result)

print(f"\nTime: {time.time() - start:.2f}s")



# from intent_router import route_command

# tests = [
#     # "Add a task to learn Kubernetes tomorrow",
#     # "Open YouTube",
#     # "Show my stats",
#     # "Mark learn Docker as complete",
#     # "Open GitHub",
#     # "Open VS Code",
#     # "Create a task to revise DSA next week",
#     "Remind me to call mom tomorrow",
#     "How many pending tasks do I have",
# ]

# for t in tests:
#     print("\nCOMMAND:", t)
#     print(route_command(t))