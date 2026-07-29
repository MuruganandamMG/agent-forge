from unittest.mock import MagicMock, patch
from runtime.scheduler import run_agent

@patch("runtime.scheduler.run_reviewer", return_value="APPROVED")
@patch("runtime.scheduler.validate")
@patch("runtime.scheduler.run_tool_agent")
def test_scheduler_passes_error_on_retry(mock_tool_agent, mock_validate, mock_reviewer, tmp_path):
    mock_tool_agent.return_value = "Fixed bug"
    
    val_fail = MagicMock()
    val_fail.passed = False
    val_fail.stage = "pytest"
    val_fail.errors = "AssertionError: expected 1 got 2"

    val_pass = MagicMock()
    val_pass.passed = True

    mock_validate.side_effect = [val_fail, val_pass]

    res = run_agent("Fix bug", project_dir=str(tmp_path))

    assert mock_tool_agent.call_count == 2
    second_call_arg = mock_tool_agent.call_args_list[1][0][0]
    assert "AssertionError" in second_call_arg
