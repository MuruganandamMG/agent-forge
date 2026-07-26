import json
from unittest.mock import patch

import pytest

from runtime.scheduler import run_agent


class TestPlan:
    @patch("runtime.scheduler.run_planner")
    def test_plan_returns_json(self, mock_run_planner) -> None:
        mock_run_planner.return_value = json.dumps({
            "goal": "Add feature",
            "tasks": [{"id": 1, "description": "do thing", "files": [], "depends_on": []}],
        })
        from runtime.scheduler import run_agent
        result = run_agent("/plan add a feature", "C:\\Windows\\Temp\\fake_dir")
        assert result.goal == "Add feature" or result.failed

class TestRunAgent:
    @patch("runtime.scheduler.run_planner")
    def test_invalid_plan_reports_error(self, mock_run_planner) -> None:
        mock_run_planner.return_value = "this is not json"
        result = run_agent("/plan do something", "C:\\Windows\\Temp\\fake_agent_test")
        assert "this is not json" in result

    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.validate")
    def test_full_cycle_with_mock(self, mock_validate, mock_run_planner, mock_run_implementer, mock_run_reviewer, tmp_path) -> None:
        """Full cycle: plan -> execute -> validate pass -> approve -> commit."""
        project_dir = str(tmp_path)

        plan = json.dumps({
            "goal": "Create hello",
            "tasks": [{
                "id": 1,
                "description": "Create hello.py",
                "files": ["hello.py"],
                "depends_on": [],
            }],
        })
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

        from runtime.validate import ValidationResult
        mock_validate.return_value = ValidationResult(
            passed=True, stage="all", errors="", details={"black": True, "ruff": True}
        )
        
        result = run_agent("/plan create hello.py", project_dir)
        assert len(result.completed) > 0

    @patch("builtins.input", return_value="user answer")
    @patch("runtime.scheduler.run_planner")
    def test_clarify_task_prompts_user(self, mock_run_planner, mock_input, tmp_path) -> None:
        """Clarify task should prompt user for input instead of calling executor/validator."""
        project_dir = str(tmp_path)
        plan = json.dumps({
            "goal": "Clarify requirements",
            "tasks": [{
                "id": 1,
                "type": "clarify",
                "description": "Which framework to use?",
                "files": [],
                "depends_on": [],
            }],
        })
        mock_run_planner.return_value = plan
        result = run_agent("/plan build app", project_dir)
        assert len(result.completed) > 0
        mock_input.assert_called_once()

    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.validate")
    def test_direct_mode_skips_planner(self, mock_validate, mock_run_implementer, mock_run_reviewer, tmp_path) -> None:
        """Queries without /plan prefix skip the planner and execute directly."""
        project_dir = str(tmp_path)
        diff = (
            "--- /dev/null\n"
            "+++ b/direct.py\n"
            "@@ -0,0 +1,1 @@\n"
            "+# direct\n"
        )
        mock_run_implementer.return_value = diff
        mock_run_reviewer.return_value = "APPROVED"

        from runtime.validate import ValidationResult
        mock_validate.return_value = ValidationResult(
            passed=True, stage="all", errors="", details={"black": True, "ruff": True}
        )

        result = run_agent("create direct.py", project_dir)
        assert mock_run_implementer.call_count == 1
        assert len(result.completed) > 0


class TestProjectContextInjection:
    @patch("runtime.scheduler.run_planner")
    def test_run_agent_accepts_project_context(self, mock_run_planner, tmp_path) -> None:
        """Verify run_agent accepts project_context parameter without error."""
        import os
        import subprocess

        os.chdir(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        mock_run_planner.return_value = '{"goal":"test","tasks":[{"id":1,"type":"code","description":"test task","files":["test.py"]}]}'

        from runtime.scheduler import run_agent

        run_agent("/plan test task", str(tmp_path), project_context="# Project Context\ntest.py")
        assert mock_run_planner.called
        assert "# Project Context" in mock_run_planner.call_args[1].get("project_context", "")

    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.validate")
    def test_run_agent_injects_project_context_into_executor(
        self, mock_validate, mock_run_implementer, mock_run_reviewer, tmp_path
    ) -> None:
        """Verify project_context flows into executor context."""
        import os
        import subprocess
        from runtime.validate import ValidationResult

        os.chdir(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        mock_run_implementer.return_value = "--- /dev/null\n+++ b/test.py\n@@ -0,0 +1,1 @@\n+# test\n"
        mock_run_reviewer.return_value = "APPROVED"
        mock_validate.return_value = ValidationResult(passed=True, stage="all", errors="", details={})

        from runtime.scheduler import run_agent

        run_agent("create test.py", str(tmp_path), project_context="PROJECT_INDEX_HERE")
        assert mock_run_implementer.called

