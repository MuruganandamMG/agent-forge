from unittest.mock import MagicMock
from runtime.subagents.tool_agent import run_tool_agent
from runtime.tools.base import Tool, ToolResult, tool

@tool(description="Read file mock")
def mock_read(path: str) -> str:
    return "content inside file"

def test_run_tool_agent_loop():
    provider_mock = MagicMock()

    # First turn: model requests function call
    call_mock = MagicMock()
    call_mock.name = "mock_read"
    call_mock.args = {"path": "test.txt"}

    provider_mock.chat_with_tools.side_effect = [
        ("Calling tool read", [call_mock]),
        ("File read complete: content inside file", None)
    ]

    result = run_tool_agent(
        task_desc="Read test.txt",
        tools=[Tool(mock_read)],
        provider=provider_mock,
        max_turns=3
    )

    assert "File read complete" in result
    assert provider_mock.chat_with_tools.call_count == 2
