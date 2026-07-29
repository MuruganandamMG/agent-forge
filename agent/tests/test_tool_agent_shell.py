from unittest.mock import MagicMock
from runtime.subagents.tool_agent import run_tool_agent
from runtime.tools.shell_tool import bash

def test_tool_agent_with_bash_execution():
    provider_mock = MagicMock()

    call_mock = MagicMock()
    call_mock.name = "bash"
    call_mock.args = {"command": "echo 'built successfully'"}

    provider_mock.chat_with_tools.side_effect = [
        ("Running build command", [call_mock]),
        ("Build completed successfully", None)
    ]

    result = run_tool_agent(
        task_desc="Run build command",
        tools=[bash],
        provider=provider_mock,
        max_turns=3
    )

    assert "Build completed successfully" in result
    assert provider_mock.chat_with_tools.call_count == 2
