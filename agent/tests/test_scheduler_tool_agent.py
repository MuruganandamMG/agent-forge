from unittest.mock import MagicMock, patch
from runtime.scheduler import run_agent

@patch("runtime.scheduler.run_reviewer", return_value="APPROVED")
@patch("runtime.scheduler.validate")
@patch("runtime.scheduler.run_tool_agent")
def test_run_agent_uses_tool_agent(mock_tool_agent, mock_validate, mock_reviewer, tmp_path):
    mock_tool_agent.return_value = "Task completed with tools"
    mock_val_res = MagicMock()
    mock_val_res.passed = True
    mock_validate.return_value = mock_val_res

    res = run_agent("Fix bug in main.py", project_dir=str(tmp_path))

    mock_tool_agent.assert_called_once()
    assert res["completed"] == ["Fix bug in main.py"]
