from collections import deque

class ConversationManager:
    def __init__(self, max_messages=20):
        self.history = deque(maxlen=max_messages)

    def add_message(self, role, content):
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")

        self.history.append({
            "role": role,
            "content": content.strip()
        })

    def add_user(self, message):
        self.add_message("user", message)

    def add_assistant(self, message):
        self.add_message("assistant", message)

    def get_history(self):
        return list(self.history)

    def clear(self):
        self.history.clear()