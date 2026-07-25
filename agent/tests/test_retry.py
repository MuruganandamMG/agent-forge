import json
from unittest.mock import MagicMock, patch

import pytest

from runtime.scheduler import run_agent
from runtime.validate import ValidationResult


class TestRetryLoop:
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.chat")
    @patch("runtime.scheduler.Sandbox")
    def test_retry_injects_error_context(self, MockSandbox, mock_chat, mock_validate) -> None:
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
        mock_chat.side_effect = [plan, diff, diff, diff]

        mock_validate.return_value = ValidationResult(
            passed=False, stage="ruff", errors="E501 line too long", details={"ruff": False}
        )

        result = run_agent("/plan fix bug", "/fake/dir")
        assert "failed" in result.lower() or "❌" in result

        # The chat function should have been called 4 times: 1 for plan + 3 retry attempts
        assert mock_chat.call_count == 4
        # Verify the second executor call (attempt 2) contains the previous error
        retry_prompt = mock_chat.call_args_list[2][0][0][1]["content"]
        assert "PREVIOUS ATTEMPT FAILED" in retry_prompt
        assert "E501 line too long" in retry_prompt
