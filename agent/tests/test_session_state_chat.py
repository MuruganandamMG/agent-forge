import pytest
from runtime.session_state import SessionState, load_session_state, save_session_state
import json
import os

def test_session_state_chat_history_init():
    state = SessionState()
    assert state.chat_history == []

def test_append_chat_message():
    state = SessionState()
    for i in range(15):
        state.append_chat_message("user", f"msg {i}")
    
    assert len(state.chat_history) == 10
    assert state.chat_history[0]["content"] == "msg 5"
    assert state.chat_history[-1]["content"] == "msg 14"

def test_save_load_chat_history(tmp_path):
    state = SessionState()
    state.append_chat_message("user", "hello")
    state.append_chat_message("assistant", "hi")
    
    save_session_state(state, str(tmp_path))
    
    loaded = load_session_state(str(tmp_path))
    assert loaded.chat_history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"}
    ]
