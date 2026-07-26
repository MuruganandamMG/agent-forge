"""End-to-end verification test for minimal CLI agent workflow."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.context import build_context, load_agents_md
from runtime.filetree import generate_filetree
from runtime.gate import classify_input
from runtime.sandbox import Sandbox
from runtime.scheduler import run_agent
from runtime.validate import ValidationResult, validate


class TestEndToEndLoop:
    @patch("runtime.validate._run_tool")
    @patch("runtime.context.count_tokens", return_value=100)
    @patch("runtime.models.chat")
    def test_end_to_end_loop_step_by_step(
        self, mock_chat, mock_count_tokens, mock_validate_tool, tmp_path
    ) -> None:
        """Verify minimal CLI agent workflow step-by-step:

        1. Load AGENTS.md and generate filetree.
        2. Classify user request through classify_input.
        3. Assemble context via build_context.
        4. Mock llama-server chat response returning a valid unified diff.
        5. Apply diff via Sandbox.apply_diff.
        6. Run validate() and create a git commit via Sandbox.checkpoint.
        7. Assert file modification applied cleanly, git commit created, and steps complete.
        """
        project_dir = str(tmp_path)
        project_path = Path(project_dir)

        # 1. Initialize project directory with AGENTS.md, target file, and git repo
        agents_md_content = "# Project Rules\n- Keep code clean and modular."
        (project_path / "AGENTS.md").write_text(agents_md_content, encoding="utf-8")

        target_file = project_path / "target.py"
        target_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

        sandbox = Sandbox(project_dir)
        sandbox.init_git()
        initial_commit = sandbox.checkpoint("Initial commit")
        assert initial_commit != ""

        # Step 1: Load project AGENTS.md and generate filetree
        loaded_agents_md = load_agents_md(project_dir)
        assert loaded_agents_md == agents_md_content

        file_tree = generate_filetree(project_dir)
        assert "AGENTS.md" in file_tree
        assert "target.py" in file_tree

        # Step 2: Pass user request through classify_input
        user_request = "Add goodbye function to target.py"
        intent = classify_input(user_request, project_context=file_tree)
        assert intent == "task"

        # Step 3: Assemble context with build_context including AGENTS.md and filetree
        context_str = build_context(
            query=user_request,
            agents_md=loaded_agents_md,
            file_tree=file_tree,
        )
        assert "AGENTS.MD" in context_str
        assert "FILE TREE" in context_str
        assert agents_md_content in context_str

        # Step 4: Mock llama-server response returning a valid unified git diff
        valid_diff = (
            "--- a/target.py\n"
            "+++ b/target.py\n"
            "@@ -1,2 +1,6 @@\n"
            " def hello():\n"
            "     return 'world'\n"
            "+\n"
            "+\n"
            "+def goodbye():\n"
            "+    return 'bye'\n"
        )
        mock_chat.return_value = valid_diff

        # LLM response (mocked llama-server response)
        llm_response = mock_chat([
            {"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": f"Context:\n{context_str}\n\nTask: {user_request}"},
        ])
        assert llm_response == valid_diff

        # Step 5: Apply diff via Sandbox.apply_diff
        applied_cleanly = sandbox.apply_diff(llm_response)
        assert applied_cleanly is True

        # Assert file modification is applied cleanly
        modified_text = target_file.read_text(encoding="utf-8")
        assert "def goodbye():" in modified_text
        assert "return 'bye'" in modified_text

        # Step 6: Run validate() and create a git commit via Sandbox.checkpoint
        mock_validate_tool.return_value = {"returncode": 0, "stdout": "", "stderr": ""}
        v_result = validate(project_dir, run_pytest=True)
        assert v_result.passed is True
        assert v_result.stage == "all"

        commit_hash = sandbox.checkpoint(f"Completed: {user_request}")
        assert commit_hash != ""
        assert commit_hash != initial_commit

        # Final verification: git status should be clean after commit
        git_status = sandbox._run_git("status", "--porcelain")
        assert git_status.stdout.strip() == ""

    @patch("builtins.input", return_value="y")
    @patch("runtime.validate._run_tool")
    @patch("runtime.scheduler.run_reviewer")
    @patch("runtime.scheduler.run_implementer")
    def test_end_to_end_agent_runner(
        self, mock_run_implementer, mock_run_reviewer, mock_validate_tool, mock_input, tmp_path
    ) -> None:
        """Verify run_agent integration loop completes end-to-end with approval and commit."""
        project_dir = str(tmp_path)
        project_path = Path(project_dir)

        (project_path / "AGENTS.md").write_text("# Rules\n- Test", encoding="utf-8")
        (project_path / "app.py").write_text("x = 1\n", encoding="utf-8")

        valid_diff = (
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1,1 +1,2 @@\n"
            " x = 1\n"
            "+y = 2\n"
        )
        mock_run_implementer.return_value = valid_diff
        mock_run_reviewer.return_value = "APPROVED"
        mock_validate_tool.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

        with patch("runtime.scheduler.enrich_request", return_value="add y to app.py"):
            with patch("runtime.context.count_tokens", return_value=100):
                res = run_agent("add y to app.py", project_dir)
        modified_content = (project_path / "app.py").read_text(encoding="utf-8")
        assert "y = 2" in modified_content
