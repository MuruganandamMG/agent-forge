# Forge v2: Phase 1 (Multi-Model Provider) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `models.py` into a provider architecture to support Gemini, Anthropic, OpenAI, and Local (Ollama) models seamlessly.

**Architecture:** Create a base provider class. Implement specific providers. Make `models.py` a router that detects the requested provider from the `--model` string (e.g., `openai/gpt-4o`, `anthropic/claude-3-5-sonnet-20240620`, `ollama/llama3`).

**Tech Stack:** Python 3, `google-genai`, `httpx` (for REST API fallback to avoid heavy SDK bloat for Anthropic/OpenAI/Ollama).

## Global Constraints

- Standard unified git diff format (`diff -u`) for patches.
- No swallowed errors: catch and raise appropriate exceptions.
- All code goes in `E:/AI/Models/agent-forge/agent/`.
- Fall back to standard `httpx` POST requests for OpenAI/Anthropic/Ollama to keep dependencies minimal, utilizing the existing `httpx` in requirements.

---

### Task 1: Create Provider Base Interface

**Files:**
- Create: `agent/runtime/providers/__init__.py`
- Create: `agent/runtime/providers/base.py`
- Create: `agent/tests/test_provider_base.py`

**Interfaces:**
- Produces: `BaseProvider` abstract class with `chat()` and `count_tokens()` methods.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from runtime.providers.base import BaseProvider

def test_base_provider_abstract():
    class IncompleteProvider(BaseProvider):
        pass
    
    with pytest.raises(TypeError):
        IncompleteProvider()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_provider_base.py -v`
Expected: FAIL (missing module)

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agent/tests/test_provider_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/providers/ agent/tests/test_provider_base.py
git commit -m "feat: add base provider interface"
```

---

### Task 2: Refactor Gemini Provider

**Files:**
- Create: `agent/runtime/providers/gemini_provider.py`
- Modify: `agent/runtime/models.py`
- Modify: `agent/tests/test_models.py`

**Interfaces:**
- Consumes: Existing Gemini logic from `models.py`.
- Produces: `GeminiProvider` class. `models.py` router.

- [ ] **Step 1: Write the implementation for `gemini_provider.py`**

Move the logic from `models.py` into this class.

```python
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

        config = types.GenerateContentConfig(temperature=temperature)
        if stop: config.stop_sequences = stop
        if system_instruction: config.system_instruction = system_instruction

        response = self.client.models.generate_content(model=self.model_name, contents=contents, config=config)
        return response.text if response.text else ""

    def count_tokens(self, text: str) -> int:
        return len(text) // 4 if text else 0
```

- [ ] **Step 2: Update `models.py` to route to providers**

```python
import sys
from typing import Any
from runtime.providers.gemini_provider import GeminiProvider

if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try: sys.stderr.reconfigure(encoding="utf-8")
        except Exception: pass

def get_provider(model_string: str = "gemini-2.5-pro"):
    """Factory to get the correct provider based on model string."""
    # Future: parse "openai/gpt-4o", etc.
    return GeminiProvider(model_name=model_string)

def chat(messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 4096, stop: list[str] | None = None, model: str = "gemini-2.5-pro") -> str:
    provider = get_provider(model)
    return provider.chat(messages, temperature, max_tokens, stop)

def count_tokens(text: str, model: str = "gemini-2.5-pro") -> int:
    provider = get_provider(model)
    return provider.count_tokens(text)
```

- [ ] **Step 3: Update `agent/tests/test_models.py`**

Update the imports and patches to target `runtime.providers.gemini_provider.genai.Client`.

```python
import pytest
from unittest.mock import patch, MagicMock
from runtime.models import chat, count_tokens

class TestChat:
    @patch("runtime.providers.gemini_provider.genai.Client")
    def test_chat_returns_assistant_content(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "I am an AI."
        mock_client.models.generate_content.return_value = mock_response

        result = chat([{"role": "user", "content": "hi"}])
        assert result == "I am an AI."

    @patch("runtime.providers.gemini_provider.genai.Client")
    def test_chat_sends_correct_parameters(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_client.models.generate_content.return_value = mock_response

        chat([{"role": "user", "content": "hi"}], temperature=0.7)
        _, kwargs = mock_client.models.generate_content.call_args
        assert kwargs["model"] == "gemini-2.5-pro"
        assert kwargs["config"].temperature == 0.7

class TestCountTokens:
    def test_count_tokens_empty_string(self):
        assert count_tokens("") == 0

    def test_count_tokens_400_chars(self):
        assert count_tokens("a" * 400) == 100
```

- [ ] **Step 4: Run tests**

Run: `pytest agent/tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/providers/gemini_provider.py agent/runtime/models.py agent/tests/test_models.py
git commit -m "refactor: extract gemini logic into dedicated provider"
```

---

### Task 3: Implement Ollama Provider

**Files:**
- Create: `agent/runtime/providers/ollama_provider.py`
- Modify: `agent/runtime/models.py`

**Interfaces:**
- Produces: `OllamaProvider` using `httpx` to POST to `http://localhost:11434/api/chat`.

- [ ] **Step 1: Write `ollama_provider.py`**

```python
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
```

- [ ] **Step 2: Update `models.py` Router**

```python
from runtime.providers.ollama_provider import OllamaProvider

def get_provider(model_string: str = "gemini-2.5-pro"):
    """Factory to get the correct provider based on model string."""
    if model_string.startswith("ollama/"):
        model_name = model_string.split("/", 1)[1]
        return OllamaProvider(model_name=model_name)
    
    if model_string.startswith("gemini/"):
        model_name = model_string.split("/", 1)[1]
        return GeminiProvider(model_name=model_name)
        
    return GeminiProvider(model_name=model_string)
```

- [ ] **Step 3: Commit**

```bash
git add agent/runtime/providers/ollama_provider.py agent/runtime/models.py
git commit -m "feat: add ollama local model provider"
```
