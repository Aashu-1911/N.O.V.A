from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize connection/session and warm the model."""
        pass

    @abstractmethod
    def health(self) -> bool:
        """Return True if the provider is healthy and model is available."""
        pass

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Sync text generation. Returns full completed text."""
        pass

    @abstractmethod
    def stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Iterator[str]:
        """Stream text generation. Yields string chunks as they arrive."""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Sync chat conversation. Returns full assistant response text."""
        pass

    @abstractmethod
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """Stream chat conversation. Yields assistant response chunks."""
        pass

    @abstractmethod
    def structured_output(self, prompt: str, schema: Any, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON output."""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel current requests."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown connection pools."""
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Return True if tools are natively supported."""
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return True if streaming is supported."""
        pass

    @abstractmethod
    def supports_json(self) -> bool:
        """Return True if native JSON mode is supported."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the model associated with this provider."""
        pass
