import json
from unittest.mock import MagicMock, patch

import pytest

from runtime.scheduler import run_agent
from runtime.validate import ValidationResult


class TestRetryLoop:
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.Sandbox")
    def test_retry_injects_error_context(self, MockSandbox, mock_run_planner, mock_run_implementer, mock_validate) -> None:
        """On validation failure, the retry call should include the error in the prompt."""
        mock_sb = MockSandbox.return_value
        mock_sb.init_git.return_value = None
        mock_sb.apply_diff.return_value = True
        mock_sb._run_git.return_value = MagicMock(stdout="")

        plan = json.dumps({
            "goal": "fix bug",
            "tasks": [{"id": 1, "description": "fix it", "files": ["f.py"], "depends_on": []}],
        })
        diff = "--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-old\n+new\n"
        mock_run_planner.return_value = plan
        mock_run_implementer.side_effect = [diff, diff, diff]

        mock_validate.return_value = ValidationResult(
            passed=False, stage="ruff", errors="E501 line too long", details={"ruff": False}
        )

        with patch("runtime.context.count_tokens", return_value=100):
            result = run_agent("/plan fix bug", "/fake/dir")
        assert "failed" in result.get("summary", "").lower() or "❌" in result.get("summary", "")

        # Implementer should have been called 3 times (MAX_RETRIES)
        assert mock_run_implementer.call_count == 3
        
        # Verify the second executor call (attempt 2) contains the previous error in the feedback kwarg
        _, kwargs = mock_run_implementer.call_args_list[1]
        retry_prompt = kwargs.get("feedback", "")
        assert "E501 line too long" in retry_prompt
