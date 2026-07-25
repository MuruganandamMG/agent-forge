import json
from unittest.mock import patch

import pytest

from runtime.scheduler import _execute, _plan, run_agent


class TestPlan:
    @patch("runtime.scheduler.chat")
    def test_plan_returns_json(self, mock_chat) -> None:
        mock_chat.return_value = json.dumps({
            "goal": "Add feature",
            "tasks": [{"id": 1, "description": "do thing", "files": [], "depends_on": []}],
        })
        result = _plan("add a feature")
        assert "goal" in result
        assert "tasks" in result


class TestExecute:
    @patch("runtime.scheduler.chat")
    def test_execute_returns_diff(self, mock_chat) -> None:
        mock_chat.return_value = "--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-old\n+new\n"
        result = _execute(
            {"id": 1, "description": "fix bug", "files": ["f.py"]},
            file_contents="old\n",
            style="",
        )
        assert "---" in result
        assert "+new" in result


class TestRunAgent:
    @patch("runtime.scheduler.chat")
    def test_invalid_plan_reports_error(self, mock_chat) -> None:
        mock_chat.return_value = "this is not json"
        result = run_agent("/plan do something", "C:\\Windows\\Temp\\fake_agent_test")
        assert result == "this is not json"

    @patch("builtins.input", return_value="y")
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.chat")
    def test_full_cycle_with_mock(self, mock_chat, mock_validate, mock_input, tmp_path) -> None:
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
        mock_chat.side_effect = [plan, diff]

        from runtime.validate import ValidationResult

        mock_validate.return_value = ValidationResult(
            passed=True, stage="all", errors="", details={"black": True, "ruff": True}
        )
        result = run_agent("/plan create hello.py", project_dir)
        assert "✅" in result or "done" in result.lower()

    @patch("builtins.input", return_value="user answer")
    @patch("runtime.scheduler.chat")
    def test_clarify_task_prompts_user(self, mock_chat, mock_input, tmp_path) -> None:
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
        mock_chat.return_value = plan
        result = run_agent("/plan build app", project_dir)
        assert "✅ Task 1" in result
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="y")
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.chat")
    def test_direct_mode_skips_planner(self, mock_chat, mock_validate, mock_input, tmp_path) -> None:
        """Queries without /plan prefix skip the planner and execute directly."""
        project_dir = str(tmp_path)
        diff = (
            "--- /dev/null\n"
            "+++ b/direct.py\n"
            "@@ -0,0 +1,1 @@\n"
            "+# direct\n"
        )
        mock_chat.return_value = diff

        from runtime.validate import ValidationResult

        mock_validate.return_value = ValidationResult(
            passed=True, stage="all", errors="", details={"black": True, "ruff": True}
        )

        result = run_agent("create direct.py", project_dir)
        assert mock_chat.call_count == 1
        assert "✅ Task 1" in result


class TestProjectContextInjection:
    @patch("runtime.scheduler.chat")
    def test_run_agent_accepts_project_context(self, mock_chat, tmp_path) -> None:
        """Verify run_agent accepts project_context parameter without error."""
        import os
        import subprocess

        os.chdir(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        mock_chat.return_value = '{"goal":"test","tasks":[{"id":1,"type":"code","description":"test task","files":["test.py"]}]}'

        from runtime.scheduler import run_agent

        run_agent("/plan test task", str(tmp_path), project_context="# Project Context\ntest.py")
        assert mock_chat.called
        messages = mock_chat.call_args[0][0]
        context_messages = [m for m in messages if "CONTEXT:\n# Project Context" in m.get("content", "")]
        assert len(context_messages) == 1

    @patch("builtins.input", return_value="y")
    @patch("runtime.scheduler.validate")
    @patch("runtime.scheduler.chat")
    def test_run_agent_injects_project_context_into_executor(
        self, mock_chat, mock_validate, mock_input, tmp_path
    ) -> None:
        """Verify project_context flows into executor context."""
        import os
        import subprocess
        from runtime.validate import ValidationResult

        os.chdir(str(tmp_path))
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        mock_chat.return_value = "--- /dev/null\n+++ b/test.py\n@@ -0,0 +1,1 @@\n+# test\n"
        mock_validate.return_value = ValidationResult(passed=True, stage="all", errors="", details={})

        from runtime.scheduler import run_agent

        run_agent("create test.py", str(tmp_path), project_context="PROJECT_INDEX_HERE")
        assert mock_chat.called
        messages = mock_chat.call_args[0][0]
        user_content = messages[1]["content"]
        assert "PROJECT_INDEX_HERE" in user_content

