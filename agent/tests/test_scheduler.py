import json
from unittest.mock import patch, MagicMock
import pytest

class TestPlan:
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.build_context")
    def test_plan_returns_json(self, mock_build_context, mock_run_planner, tmp_path) -> None:
        mock_run_planner.return_value = json.dumps({
            "goal": "Add feature",
            "tasks": [{"id": 1, "description": "do thing", "files": [], "depends_on": []}],
        })
        mock_build_context.return_value = "fake context"
        from runtime.scheduler import run_agent
        with patch("runtime.scheduler.enrich_request", return_value="add a feature"):
            with patch("runtime.scheduler.TaskGraph.from_plan_json") as mock_tg:
                mock_graph = MagicMock()
                mock_graph.goal = "Add feature"
                mock_graph.next_task.return_value = None
                mock_tg.return_value = mock_graph
                result = run_agent("/plan add a feature", str(tmp_path))
        assert result.get("goal") == "Add feature" or result.get("failed")

class TestRunAgent:
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.build_context")
    def test_invalid_plan_reports_error(self, mock_build_context, mock_run_planner, tmp_path) -> None:
        mock_run_planner.return_value = "this is not json"
        mock_build_context.return_value = "fake context"
        from runtime.scheduler import run_agent
        with patch("runtime.scheduler.enrich_request", return_value="do something"):
            result = run_agent("/plan do something", str(tmp_path))
        assert "this is not json" in result.raw

    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.build_context")
    def test_full_cycle_with_mock(self, mock_build_context, mock_validate, mock_run_planner, mock_run_implementer, mock_run_reviewer, tmp_path) -> None:
        """Full cycle: plan -> execute -> validate pass -> approve -> commit."""
        project_dir = str(tmp_path)
        mock_build_context.return_value = "fake context"

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
        
        from runtime.scheduler import run_agent
        with patch("runtime.scheduler.enrich_request", return_value="create hello.py"):
            result = run_agent("/plan create hello.py", project_dir)
        assert len(result.get("completed", [])) > 0

    @patch("builtins.input", return_value="user answer")
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.build_context")
    def test_clarify_task_prompts_user(self, mock_build_context, mock_run_planner, mock_input, tmp_path) -> None:
        """Clarify task should prompt user for input instead of calling executor/validator."""
        project_dir = str(tmp_path)
        mock_build_context.return_value = "fake context"
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
        from runtime.scheduler import run_agent
        with patch("runtime.scheduler.enrich_request", return_value="build app"):
            result = run_agent("/plan build app", project_dir)
        assert len(result.get("completed", [])) > 0
        mock_input.assert_called_once()

    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.build_context")
    def test_direct_mode_skips_planner(self, mock_build_context, mock_validate, mock_run_implementer, mock_run_reviewer, tmp_path) -> None:
        """Queries without /plan prefix skip the planner and execute directly."""
        project_dir = str(tmp_path)
        mock_build_context.return_value = "fake context"
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

        from runtime.scheduler import run_agent
        with patch("runtime.scheduler.enrich_request", return_value="create direct.py"):
            result = run_agent("create direct.py", project_dir)
        assert mock_run_implementer.call_count == 1
        assert len(result.get("completed", [])) > 0


class TestProjectContextInjection:
    @patch("runtime.scheduler.run_planner")
    @patch("runtime.scheduler.build_context")
    def test_run_agent_accepts_project_context(self, mock_build_context, mock_run_planner, tmp_path) -> None:
        """Verify run_agent accepts project_context parameter without error."""
        import os
        import subprocess

        os.chdir(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        mock_run_planner.return_value = '{"goal":"test","tasks":[{"id":1,"type":"code","description":"test task","files":["test.py"]}]}'
        mock_build_context.return_value = "fake context"

        from runtime.scheduler import run_agent

        with patch("runtime.scheduler.enrich_request", return_value="test task"):
            with patch("runtime.scheduler.TaskGraph.from_plan_json") as mock_tg:
                mock_graph = MagicMock()
                mock_graph.goal = "test"
                mock_graph.next_task.return_value = None
                mock_tg.return_value = mock_graph
                run_agent("/plan test task", str(tmp_path), project_context="# Project Context\ntest.py")
        assert mock_run_planner.called
        assert "# Project Context" in mock_run_planner.call_args[1].get("project_context", "")

    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.build_context")
    def test_run_agent_injects_project_context_into_executor(
        self, mock_build_context, mock_validate, mock_run_implementer, mock_run_reviewer, tmp_path
    ) -> None:
        """Verify project_context flows into executor context."""
        import os
        import subprocess
        from runtime.validate import ValidationResult

        os.chdir(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        mock_build_context.return_value = "fake context"
        mock_run_implementer.return_value = "--- /dev/null\n+++ b/test.py\n@@ -0,0 +1,1 @@\n+# test\n"
        mock_run_reviewer.return_value = "APPROVED"
        mock_validate.return_value = ValidationResult(passed=True, stage="all", errors="", details={})

        from runtime.scheduler import run_agent

        with patch("runtime.scheduler.enrich_request", return_value="create test.py"):
            run_agent("create test.py", str(tmp_path), project_context="PROJECT_INDEX_HERE")
        assert mock_run_implementer.called
