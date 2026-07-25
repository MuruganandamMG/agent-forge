import pytest
from unittest.mock import patch
from runtime.chat_responder import generate_chat_response

@patch("runtime.chat_responder.chat")
def test_generate_chat_response(mock_chat):
    mock_chat.return_value = "Hello! I am Forge."
    history = [{"role": "user", "content": "hi"}]
    
    res = generate_chat_response("how are you?", history, "File: main.py")
    
    assert res == "Hello! I am Forge."
    mock_chat.assert_called_once()
    
    # Verify messages format
    messages = mock_chat.call_args[0][0]
    assert messages[0]["role"] == "system"
    assert "Forge Coding Agent" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hi"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "how are you?"

@patch("runtime.chat_responder.chat")
def test_generate_chat_response_fallback(mock_chat):
    mock_chat.side_effect = Exception("API error")
    res = generate_chat_response("hi", [], "")
    assert "Tell me what you'd like me to build" in res
    assert "API error" in res
