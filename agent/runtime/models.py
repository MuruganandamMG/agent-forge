import sys
from typing import Any
from runtime.providers.gemini_provider import GeminiProvider
from runtime.providers.ollama_provider import OllamaProvider

if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def get_provider(model_string: str = "gemini-2.5-pro"):
    """Factory to get the correct provider based on model string."""
    if model_string.startswith("ollama/"):
        model_name = model_string.split("/", 1)[1]
        return OllamaProvider(model_name=model_name)
    
    if model_string.startswith("gemini/"):
        model_name = model_string.split("/", 1)[1]
        return GeminiProvider(model_name=model_name)
        
    return GeminiProvider(model_name=model_string)


def chat(
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 4096,
    stop: list[str] | None = None,
    model: str = "gemini-2.5-pro"
) -> str:
    """Send a chat completion request to an LLM API and return the assistant response text."""
    provider = get_provider(model)
    return provider.chat(messages, temperature, max_tokens, stop)


def count_tokens(text: str, model: str = "gemini-2.5-pro") -> int:
    """Estimate token count using the provider's token counter."""
    # Fast path to avoid initializing a client just to count tokens in tests
    if not text:
        return 0
    return len(text) // 4
