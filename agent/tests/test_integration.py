"""End-to-end integration tests for the local coding agent."""

import json
from unittest.mock import patch

import pytest

from runtime.scheduler import run_agent


class TestEndToEnd:
    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.run_planner")
    def test_full_cycle_creates_file(self, mock_run_planner, mock_run_implementer, mock_run_reviewer, tmp_path) -> None:
        """Full cycle: plan -> execute -> validate -> apply -> commit."""
        project_dir = str(tmp_path)

        # Plan response
        plan = json.dumps({
            "goal": "Create a hello world script",
            "tasks": [{
                "id": 1,
                "description": "Create hello.py that prints hello world",
                "files": ["hello.py"],
                "depends_on": [],
            }],
        })

        # Executor response: a diff that creates hello.py
        diff = (
            "--- /dev/null\n"
            "+++ b/hello.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+def main():\n"
            "+    print('hello world')\n"
        )

        mock_run_planner.return_value = plan
        mock_run_implementer.return_value = diff
        mock_run_reviewer.return_value = "APPROVED"

        with patch("runtime.scheduler.validate") as mock_validate:
            from runtime.validate import ValidationResult

            mock_validate.return_value = ValidationResult(
                passed=True, stage="all", errors="", details={"black": True, "ruff": True}
            )
            with patch("runtime.context.count_tokens", return_value=100):
                result = run_agent("/plan create hello.py", project_dir)

        assert "✅" in result.get("summary", "") or "done" in result.get("summary", "").lower()
        # Verify the file was actually created in sandbox project_dir
        hello_file = tmp_path / "hello.py"
        assert hello_file.exists()
        assert "hello world" in hello_file.read_text(encoding="utf-8")

    @patch("runtime.scheduler.run_planner")
    def test_invalid_plan_reports_error(self, mock_run_planner, tmp_path) -> None:
        """If the planner returns non-JSON, the agent should return the raw message."""
        mock_run_planner.return_value = "this is not json"
        with patch("runtime.context.count_tokens", return_value=100):
            result = run_agent("/plan do something", str(tmp_path))
        assert "this is not json" in result.raw
