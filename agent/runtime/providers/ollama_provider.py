import httpx
from typing import Any
from runtime.providers.base import BaseProvider

class OllamaProvider(BaseProvider):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def chat(self, messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 4096, stop: list[str] | None = None) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if stop:
            payload["options"]["stop"] = stop
            
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")

    def count_tokens(self, text: str) -> int:
        return len(text) // 4 if text else 0
