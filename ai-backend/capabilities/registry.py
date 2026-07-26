import threading
from typing import Dict, List, Optional
from capabilities.base import BaseCapability

class CapabilityRegistry:
    """Thread-safe registration repository for N.O.V.A. subsystem capabilities."""
    
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._capabilities: Dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability) -> None:
        """Register a new capability instance."""
        with self._lock:
            name = capability.__class__.__name__
            self._capabilities[name] = capability

    def unregister(self, name: str) -> None:
        """Unregister a capability by its class name."""
        with self._lock:
            self._capabilities.pop(name, None)

    def get_all(self) -> List[BaseCapability]:
        """Return all registered capabilities."""
        with self._lock:
            return list(self._capabilities.values())

    def get(self, name: str) -> Optional[BaseCapability]:
        """Retrieve a specific capability by class name."""
        with self._lock:
            return self._capabilities.get(name)

    def clear(self) -> None:
        """Unregister all capabilities."""
        with self._lock:
            self._capabilities.clear()


# Global Singleton Registry Instance
_registry = CapabilityRegistry()

def register_capability(capability: BaseCapability) -> None:
    """Helper function to register a capability with the global central registry."""
    _registry.register(capability)

def unregister_capability(name: str) -> None:
    """Helper function to unregister a capability from the central registry."""
    _registry.unregister(name)

def get_registered_capabilities() -> List[BaseCapability]:
    """Helper function to retrieve all currently registered capabilities."""
    return _registry.get_all()
