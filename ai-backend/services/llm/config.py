import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class LLMConfig:
    def __init__(self, config_path: Optional[str] = None):
        # Look for llm_config.json in the project root
        self.config_path = config_path or os.getenv("LLM_CONFIG_PATH") or str(Path(__file__).parents[2] / "llm_config.json")
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        defaults = {
            "ollama_url": "http://localhost:11434",
            "default_model": "hermes3:8b",
            "fallback_model": "qwen3:8b",
            "temperature": 0.2,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "context_length": 2048,
            "timeout": 60.0,
            "streaming": True,
            "json_mode": False,
            "system_prompt": "You are N.O.V.A., a smart personal desktop AI assistant."
        }
        path = Path(self.config_path)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    defaults.update(file_data)
            except Exception as e:
                print(f"[LLM CONFIG ERROR] Failed to load config from {self.config_path}: {e}")
        
        # Override with environment variables if present
        if os.getenv("OLLAMA_URL"):
            defaults["ollama_url"] = os.getenv("OLLAMA_URL")
        if os.getenv("OLLAMA_MODEL"):
            defaults["default_model"] = os.getenv("OLLAMA_MODEL")
            
        return defaults

    @property
    def ollama_url(self) -> str:
        return self.data.get("ollama_url", "http://localhost:11434")

    @property
    def default_model(self) -> str:
        return self.data.get("default_model", "hermes3:8b")

    @property
    def fallback_model(self) -> str:
        return self.data.get("fallback_model", "qwen3:8b")

    @property
    def temperature(self) -> float:
        return float(self.data.get("temperature", 0.2))

    @property
    def top_p(self) -> float:
        return float(self.data.get("top_p", 0.9))

    @property
    def repeat_penalty(self) -> float:
        return float(self.data.get("repeat_penalty", 1.1))

    @property
    def context_length(self) -> int:
        return int(self.data.get("context_length", 2048))

    @property
    def timeout(self) -> float:
        return float(self.data.get("timeout", 60.0))

    @property
    def streaming(self) -> bool:
        val = self.data.get("streaming", True)
        if isinstance(val, str):
            return val.lower() == "true"
        return bool(val)

    @property
    def json_mode(self) -> bool:
        val = self.data.get("json_mode", False)
        if isinstance(val, str):
            return val.lower() == "true"
        return bool(val)

    @property
    def system_prompt(self) -> str:
        return self.data.get("system_prompt", "You are N.O.V.A., a smart personal desktop AI assistant.")
