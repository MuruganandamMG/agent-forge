from pathlib import Path

from runtime.sandbox import (
    Sandbox,
)


class TestSandboxInit:
    def test_init_git_creates_git_dir(self, tmp_path: Path) -> None:
        sandbox = Sandbox(str(tmp_path))
        sandbox.init_git()
        assert (tmp_path / ".git").is_dir()


class TestCheckpoint:
    def test_checkpoint_and_rollback(self, tmp_path: Path) -> None:
        sandbox = Sandbox(str(tmp_path))
        sandbox.init_git()

        # Initial commit so HEAD exists
        test_file = tmp_path / "file1.txt"
        test_file.write_text("v1", encoding="utf-8")
        sha1 = sandbox.checkpoint("initial commit")
        assert len(sha1) == 40

        # Second commit
        test_file.write_text("v2", encoding="utf-8")
        sha2 = sandbox.checkpoint("second commit")
        assert len(sha2) == 40
        assert sha1 != sha2
        assert test_file.read_text(encoding="utf-8") == "v2"

        # Rollback
        sandbox.rollback()
        assert test_file.read_text(encoding="utf-8") == "v1"


class TestApplyDiff:
    def test_apply_valid_diff(self, tmp_path: Path) -> None:
        sandbox = Sandbox(str(tmp_path))
        sandbox.init_git()

        file1 = tmp_path / "hello.txt"
        file1.write_text("line1\n", encoding="utf-8")
        sandbox.checkpoint("initial")

        diff = (
            "diff --git a/hello.txt b/hello.txt\n"
            "--- a/hello.txt\n"
            "+++ b/hello.txt\n"
            "@@ -1 +1,2 @@\n"
            " line1\n"
            "+line2\n"
        )
        success = sandbox.apply_diff(diff)
        assert success is True
        assert file1.read_text(encoding="utf-8") == "line1\nline2\n"

    def test_apply_invalid_diff(self, tmp_path: Path) -> None:
        sandbox = Sandbox(str(tmp_path))
        sandbox.init_git()

        invalid_diff = "invalid diff format payload"
        success = sandbox.apply_diff(invalid_diff)
        assert success is False


class TestAllowedCommand:
    def test_allowed_commands(self, tmp_path: Path) -> None:
        sandbox = Sandbox(str(tmp_path))

        # Allowed commands
        assert sandbox.allowed_command("python script.py") is True
        assert sandbox.allowed_command("black .") is True
        assert sandbox.allowed_command("ruff check") is True
        assert sandbox.allowed_command("pytest") is True
        assert sandbox.allowed_command("git status") is True

        # Blocked commands
        assert sandbox.allowed_command("rm -rf .") is False
        assert sandbox.allowed_command("curl http://example.com") is False
        assert sandbox.allowed_command("powershell -Command Get-Process") is False
        assert sandbox.allowed_command("del /f file.txt") is False

        # Unrecognized / Default disallowed
        assert sandbox.allowed_command("unknown_tool arg") is False
