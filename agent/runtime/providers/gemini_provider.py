from typing import Any
from google import genai
from google.genai import types
from runtime.providers.base import BaseProvider

class GeminiProvider(BaseProvider):
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        self.model_name = model_name
        self.client = genai.Client()

    def chat(self, messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 4096, stop: list[str] | None = None) -> str:
        system_instruction = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                if not msg.get("content", "").strip():
                    continue
                role = "model" if msg["role"] == "assistant" else msg["role"]
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        config = types.GenerateContentConfig(temperature=temperature, max_output_tokens=max_tokens)
        if stop: config.stop_sequences = stop
        if system_instruction: config.system_instruction = system_instruction

        response = self.client.models.generate_content(model=self.model_name, contents=contents, config=config)
        return response.text if response.text else ""

    def count_tokens(self, text: str) -> int:
        return len(text) // 4 if text else 0
