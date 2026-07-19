from abc import ABC, abstractmethod
from pathlib import Path

class BaseTTSEngine(ABC):

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the TTS engine, loading models or resources once."""
        pass

    @abstractmethod
    def synthesize(self, text: str) -> Path:
        """Synthesize text to a temporary WAV file and return its Path."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Release any loaded resources cleanly."""
        pass
