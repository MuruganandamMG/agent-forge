import sys
from typing import Any

from google import genai
from google.genai import types

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


def chat(
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 4096,
    stop: list[str] | None = None,
) -> str:
    """Send a chat completion request to Gemini API and return the assistant response text."""
    client = genai.Client()
    system_instruction = None
    
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        else:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            contents.append(
                types.Content(
                    role=role, 
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        stop_sequences=stop,
    )
    
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=contents,
        config=config
    )
    
    if response.text is None:
        return ""
    return response.text


def count_tokens(text: str) -> int:
    """Estimate token count using a simple chars/4 heuristic."""
    if not text:
        return 0
    return len(text) // 4
