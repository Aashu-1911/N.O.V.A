import os

VOICE_MODEL = os.getenv("VOICE_MODEL", "medium")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

VOICE_CONFIG = {
    "min_logprob": float(os.getenv("VOICE_MIN_LOGPROB", "-1.5")),
    "max_no_speech": float(os.getenv("VOICE_MAX_NO_SPEECH", "0.85")),
    "intent_override": os.getenv("VOICE_INTENT_OVERRIDE", "True").lower() == "true",
    "retry_count": int(os.getenv("VOICE_RETRY_COUNT", "2")),
    "retry_delay": float(os.getenv("VOICE_RETRY_DELAY", "0.25")),
    "diagnostics": os.getenv("VOICE_DIAGNOSTICS", "False").lower() == "true"
}