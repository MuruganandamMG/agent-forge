from unittest.mock import MagicMock, patch
from runtime.subagents.tool_agent import run_tool_agent
from runtime.tools.base import Tool, tool

@tool(description="Mock tool for rendering test")
def mock_render_tool(msg: str) -> str:
    return f"Processed {msg}"

@patch("runtime.subagents.tool_agent.render_subagent_card")
def test_tool_agent_renders_tool_cards(mock_render):
    provider_mock = MagicMock()
    call_mock = MagicMock()
    call_mock.name = "mock_render_tool"
    call_mock.args = {"msg": "hello"}

    provider_mock.chat_with_tools.side_effect = [
        ("Calling tool", [call_mock]),
        ("Done", None)
    ]

    run_tool_agent("Test task", tools=[Tool(mock_render_tool)], provider=provider_mock, max_turns=2)
    mock_render.assert_called()
