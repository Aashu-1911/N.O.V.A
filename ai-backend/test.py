from ollama_client import send_message

reply = ""

for chunk in send_message("Hello Jarvis"):
    print(chunk, end="", flush=True)
    reply += chunk

print()

