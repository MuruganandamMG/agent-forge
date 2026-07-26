import pytest
from unittest.mock import patch
from runtime.subagents.core import run_planner, run_implementer, run_reviewer

@patch("runtime.subagents.core.chat")
def test_subagent_handlers(mock_chat):
    mock_chat.return_value = "APPROVED"
    assert run_reviewer("task", "diff") == "APPROVED"
