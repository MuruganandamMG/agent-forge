from abc import ABC, abstractmethod
from typing import Any

class BaseProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 4096, stop: list[str] | None = None) -> str:
        """Send a chat completion request and return the response text."""
        pass
        
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for the given text."""
        pass
