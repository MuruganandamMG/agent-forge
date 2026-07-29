from typing import Any, List, Optional, Tuple
from google import genai
from google.genai import types
from runtime.providers.base import BaseProvider
from runtime.tools.base import Tool

class GeminiProvider(BaseProvider):
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        self.model_name = model_name
        self.client = genai.Client()

    def chat(self, messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 4096, stop: list[str] | None = None) -> str:
        text, _ = self.chat_with_tools(messages, temperature=temperature, max_tokens=max_tokens, stop=stop)
        return text

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        stop: list[str] | None = None,
    ) -> Tuple[str, Any]:
        system_instruction = None
        contents = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif "parts" in msg:
                role = "model" if msg["role"] == "assistant" else msg["role"]
                contents.append(types.Content(role=role, parts=msg["parts"]))
            else:
                if not msg.get("content", "").strip():
                    continue
                role = "model" if msg["role"] == "assistant" else msg["role"]
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        genai_tools = None
        if tools:
            declarations = [t.to_genai_declaration() for t in tools]
            genai_tools = [types.Tool(function_declarations=declarations)]

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            tools=genai_tools,
        )
        if stop: config.stop_sequences = stop
        if system_instruction: config.system_instruction = system_instruction

        response = self.client.models.generate_content(model=self.model_name, contents=contents, config=config)
        
        text = response.text if response.text else ""
        function_calls = getattr(response, "function_calls", None)
        return text, function_calls

    def count_tokens(self, text: str) -> int:
        return len(text) // 4 if text else 0
