from unittest.mock import MagicMock
from google.genai import types
from runtime.providers.gemini_provider import GeminiProvider
from runtime.tools.base import Tool, tool

@tool(description="Add numbers")
def mock_add(a: int, b: int) -> int:
    return a + b

def test_gemini_provider_chat_with_tools():
    provider = GeminiProvider(model_name="gemini-2.5-pro")
    provider.client = MagicMock()

    mock_resp = MagicMock()
    mock_resp.text = "I'll call the add function"
    mock_resp.function_calls = None
    provider.client.models.generate_content.return_value = mock_resp

    tool_obj = Tool(mock_add)
    messages = [{"role": "user", "content": "Add 2 and 3"}]

    res_text, function_calls = provider.chat_with_tools(messages=messages, tools=[tool_obj])

    assert res_text == "I'll call the add function"
    assert function_calls is None
    provider.client.models.generate_content.assert_called_once()
