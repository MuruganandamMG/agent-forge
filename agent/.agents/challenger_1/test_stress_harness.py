"""Empirical Stress Harness for CLI Agentic Coding Assistant."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.scheduler import run_agent
from runtime.validate import validate, ValidationResult
from runtime.sandbox import Sandbox
from runtime.models import find_llama_server, ensure_server, health_check, chat, strip_thinking, count_tokens


class TestSchedulerCommandParsing(unittest.TestCase):
    """Area 1: Command parsing for /plan vs direct execution in runtime/scheduler.py."""

    @patch("runtime.scheduler.Sandbox")
    @patch("runtime.scheduler.chat")
    def test_plan_mode_parsing(self, mock_chat, mock_sandbox):
        plan_json = '''{
            "goal": "Build feature X",
            "tasks": [
                {"id": 1, "type": "code", "description": "Write code for X", "files": ["x.py"]}
            ]
        }'''
        mock_chat.return_value = plan_json
        
        with patch("runtime.scheduler.validate") as mock_val, \
             patch("runtime.scheduler.input", return_value="y"):
            mock_val.return_value = ValidationResult(passed=True, stage="all", errors="")
            summary = run_agent("/plan Build feature X", str(PROJECT_ROOT))
        
        mock_chat.assert_called()
        self.assertIn("Build feature X", summary)

    @patch("runtime.scheduler.Sandbox")
    @patch("runtime.scheduler.chat")
    def test_plan_mode_with_leading_whitespace(self, mock_chat, mock_sandbox):
        plan_json = '{"goal": "Test goal", "tasks": [{"id": 1, "type": "code", "description": "Test", "files": []}]}'
        mock_chat.return_value = plan_json
        
        with patch("runtime.scheduler.validate") as mock_val, \
             patch("runtime.scheduler.input", return_value="y"):
            mock_val.return_value = ValidationResult(passed=True, stage="all", errors="")
            summary = run_agent("   /plan Test goal", str(PROJECT_ROOT))
        
        self.assertIn("Test goal", summary)

    @patch("runtime.scheduler.Sandbox")
    @patch("runtime.scheduler.chat")
    def test_planner_prefix_overlap_edge_case(self, mock_chat, mock_sandbox):
        """Edge case: /planner should match startswith('/plan') but strips only 5 chars ('/plan') leaving 'ner ...'."""
        plan_json = '{"goal": "ner test", "tasks": [{"id": 1, "type": "code", "description": "ner test", "files": []}]}'
        mock_chat.return_value = plan_json
        
        with patch("runtime.scheduler.validate") as mock_val, \
             patch("runtime.scheduler.input", return_value="y"):
            mock_val.return_value = ValidationResult(passed=True, stage="all", errors="")
            summary = run_agent("/planner test", str(PROJECT_ROOT))
        
        first_call_args = mock_chat.call_args_list[0]
        messages = first_call_args[0][0]
        user_msg = [m for m in messages if m["role"] == "user"][-1]["content"]
        self.assertEqual(user_msg, "ner test")

    @patch("runtime.scheduler.Sandbox")
    @patch("runtime.scheduler.chat")
    def test_direct_execution_mode(self, mock_chat, mock_sandbox):
        """Direct execution mode does NOT call _plan, creates single task directly."""
        mock_chat.return_value = "--- a/file.txt\n+++ b/file.txt\n@@ -0,0 +1 @@\n+hello\n"
        mock_sandbox_inst = mock_sandbox.return_value
        mock_sandbox_inst.apply_diff.return_value = True
        mock_sandbox_inst.checkpoint.return_value = "abc12345"

        with patch("runtime.scheduler.validate") as mock_val, \
             patch("runtime.scheduler.input", return_value="y"):
            mock_val.return_value = ValidationResult(passed=True, stage="all", errors="")
            summary = run_agent("Fix bug in math module", str(PROJECT_ROOT))

        self.assertIn("Fix bug in math module", summary)
        first_call_args = mock_chat.call_args_list[0]
        sys_msg = first_call_args[0][0][0]["content"]
        self.assertNotIn("You are a expert software architect", sys_msg)


class TestClarificationHandling(unittest.TestCase):
    """Area 2: Clarification task handling for clarify task type / CLARIFY: prefix."""

    @patch("runtime.scheduler.Sandbox")
    @patch("runtime.scheduler.chat")
    def test_clarify_task_type(self, mock_chat, mock_sandbox):
        plan_json = '''{
            "goal": "Clarification workflow",
            "tasks": [
                {"id": 1, "type": "clarify", "description": "Which database engine should be used?", "files": []}
            ]
        }'''
        mock_chat.return_value = plan_json

        with patch("runtime.scheduler.input", return_value="PostgreSQL") as mock_input:
            summary = run_agent("/plan Clarification workflow", str(PROJECT_ROOT))

        mock_input.assert_called_once_with("  Your answer: ")
        self.assertEqual(mock_chat.call_count, 1)

    @patch("runtime.scheduler.Sandbox")
    @patch("runtime.scheduler.chat")
    def test_clarify_prefix_in_description(self, mock_chat, mock_sandbox):
        plan_json = '''{
            "goal": "Prefix clarification workflow",
            "tasks": [
                {"id": 1, "type": "code", "description": "CLARIFY: Should we use sync or async HTTP client?", "files": []}
            ]
        }'''
        mock_chat.return_value = plan_json

        with patch("runtime.scheduler.input", return_value="httpx async") as mock_input:
            summary = run_agent("/plan Prefix clarification workflow", str(PROJECT_ROOT))

        mock_input.assert_called_once_with("  Your answer: ")
        self.assertEqual(mock_chat.call_count, 1)


class TestValidationPipeline(unittest.TestCase):
    """Area 3: Validation pipeline stage execution in runtime/validate.py."""

    @patch("runtime.validate._run_tool")
    def test_all_stages_pass(self, mock_run_tool):
        mock_run_tool.return_value = {"returncode": 0, "stdout": "Success", "stderr": ""}
        
        result = validate(str(PROJECT_ROOT), run_pytest=True)
        
        self.assertTrue(result.passed)
        self.assertEqual(result.stage, "all")
        self.assertEqual(result.details, {"black": True, "ruff": True, "pytest": True})
        self.assertEqual(mock_run_tool.call_count, 3)

    @patch("runtime.validate._run_tool")
    def test_black_failing_short_circuits(self, mock_run_tool):
        mock_run_tool.return_value = {"returncode": 1, "stdout": "would reformat foo.py", "stderr": ""}
        
        result = validate(str(PROJECT_ROOT), run_pytest=True)
        
        self.assertFalse(result.passed)
        self.assertEqual(result.stage, "black")
        self.assertIn("would reformat foo.py", result.errors)
        self.assertEqual(mock_run_tool.call_count, 1)
        self.assertEqual(result.details, {"black": False})

    @patch("runtime.validate._run_tool")
    def test_ruff_failing_short_circuits_pytest(self, mock_run_tool):
        def side_effect(cmd, cwd):
            if "black" in cmd:
                return {"returncode": 0, "stdout": "All done!", "stderr": ""}
            elif "ruff" in cmd:
                return {"returncode": 1, "stdout": "foo.py:1:1: F401 unused import", "stderr": ""}
            return {"returncode": 0, "stdout": "", "stderr": ""}

        mock_run_tool.side_effect = side_effect
        
        result = validate(str(PROJECT_ROOT), run_pytest=True)
        
        self.assertFalse(result.passed)
        self.assertEqual(result.stage, "ruff")
        self.assertEqual(mock_run_tool.call_count, 2)
        self.assertEqual(result.details, {"black": True, "ruff": False})

    @patch("runtime.validate._run_tool")
    def test_run_pytest_false_omits_pytest(self, mock_run_tool):
        mock_run_tool.return_value = {"returncode": 0, "stdout": "OK", "stderr": ""}
        
        result = validate(str(PROJECT_ROOT), run_pytest=False)
        
        self.assertTrue(result.passed)
        self.assertEqual(result.details, {"black": True, "ruff": True})
        self.assertNotIn("pytest", result.details)
        self.assertEqual(mock_run_tool.call_count, 2)


class TestSandboxSecurity(unittest.TestCase):
    """Area 4: Command blocklisting & allowlisting in runtime/sandbox.py."""

    def setUp(self):
        self.sandbox = Sandbox(str(PROJECT_ROOT))

    def test_allowlisted_commands(self):
        allowed = [
            "python main.py",
            "pytest tests/",
            "black --check .",
            "ruff check .",
            "git status",
            "git diff",
            "git log -n 5",
            "cat README.md",
            "echo Hello",
        ]
        for cmd in allowed:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.sandbox.allowed_command(cmd), f"Expected '{cmd}' to be allowed")

    def test_blocklisted_commands(self):
        blocked = [
            "rm -rf /",
            "del /f /q C:\\file.txt",
            "curl http://example.com",
            "powershell -Command Get-Process",
            "rmdir /s /q build",
            "wget http://example.com",
            "shutdown /s",
            "taskkill /f /im node.exe",
            "net user hacker",
            "reg add HKCU\\Software",
        ]
        for cmd in blocked:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.sandbox.allowed_command(cmd), f"Expected '{cmd}' to be blocked")

    def test_adversarial_bypasses(self):
        """Adversarial testing of allowed_command logic."""
        # 1. Chained commands starting with allowlisted prefix
        chained_cmd = "echo hello && rm -rf /"
        is_allowed = self.sandbox.allowed_command(chained_cmd)
        self.assertTrue(is_allowed, "Chained command starting with allowlist prefix bypasses blocklist")

        # 2. Python inline system execution
        python_exec = "python -c \"import os; os.system('rm -rf /')\""
        self.assertTrue(self.sandbox.allowed_command(python_exec))

        # 3. Disallowed git command (git commit)
        git_commit = "git commit -m 'test'"
        self.assertFalse(self.sandbox.allowed_command(git_commit), "git commit is not in allowlist")


class TestModelsServerConfig(unittest.TestCase):
    """Area 5: Server auto-location and -ngl 99 GPU offload in runtime/models.py."""

    def test_find_llama_server_env_override(self):
        fake_binary = PROJECT_ROOT / "runtime" / "models.py"  # Existing file to pass is_file()
        with patch.dict(os.environ, {"LLAMA_SERVER_PATH": str(fake_binary)}):
            server_path = find_llama_server()
            self.assertEqual(server_path, str(fake_binary))

    def test_find_llama_server_fallback(self):
        with patch.dict(os.environ, {}, clear=False):
            if "LLAMA_SERVER_PATH" in os.environ:
                del os.environ["LLAMA_SERVER_PATH"]
            with patch("shutil.which", return_value=None), \
                 patch.object(Path, "is_file", return_value=False):
                server_path = find_llama_server()
                self.assertEqual(server_path, "llama-server")

    @patch("runtime.models.health_check", return_value=False)
    @patch("subprocess.Popen")
    def test_ensure_server_gpu_offload_ngl_99(self, mock_popen, mock_health):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        mock_health.side_effect = [False, True]

        ensure_server(model_path="dummy.gguf", port=8081, ctx_size=8192, server_bin="llama-server")

        mock_popen.assert_called_once()
        cmd_args = mock_popen.call_args[0][0]

        # Verify -ngl 99 parameters
        self.assertIn("-ngl", cmd_args)
        ngl_index = cmd_args.index("-ngl")
        self.assertEqual(cmd_args[ngl_index + 1], "99")
        
        # Verify other required CLI flags
        self.assertIn("-m", cmd_args)
        self.assertIn("dummy.gguf", cmd_args)
        self.assertIn("--port", cmd_args)
        self.assertIn("8081", cmd_args)
        self.assertIn("-c", cmd_args)
        self.assertIn("8192", cmd_args)


if __name__ == "__main__":
    unittest.main()
