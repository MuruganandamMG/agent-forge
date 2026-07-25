import subprocess
from pathlib import Path

COMMAND_ALLOWLIST_PREFIXES: list[str] = [
    "python",
    "pip",
    "pytest",
    "black",
    "ruff",
    "pyright",
    "git status",
    "git diff",
    "git log",
    "cat",
    "head",
    "tail",
    "echo",
    "type",
    "dir",
]

COMMAND_BLOCKLIST_PREFIXES: list[str] = [
    "rm ",
    "del ",
    "rmdir",
    "format",
    "curl",
    "wget",
    "powershell",
    "cmd ",
    "shutdown",
    "taskkill",
    "net ",
    "reg ",
]


class Sandbox:
    """Provides git checkpointing, diff application, and command filtering for a project."""

    def __init__(self, project_dir: str) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=str(self.project_dir),
            capture_output=True,
            text=True,
        )

    def init_git(self) -> None:
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            self._run_git("init")
            self._run_git("config", "user.name", "Agent Sandbox")
            self._run_git("config", "user.email", "sandbox@agent.local")

    def checkpoint(self, message: str) -> str:
        self._run_git("add", "-A")
        self._run_git("commit", "-m", f"checkpoint: {message}", "--allow-empty")
        sha_proc = self._run_git("rev-parse", "HEAD")
        return sha_proc.stdout.strip()

    def rollback(self) -> None:
        self._run_git("reset", "--hard", "HEAD~1")

    def apply_diff(self, diff_text: str) -> bool:
        proc_check = subprocess.run(
            ["git", "apply", "--check", "-"],
            input=diff_text,
            cwd=str(self.project_dir),
            capture_output=True,
            text=True,
        )
        if proc_check.returncode != 0:
            return False

        proc_apply = subprocess.run(
            ["git", "apply", "-"],
            input=diff_text,
            cwd=str(self.project_dir),
            capture_output=True,
            text=True,
        )
        return proc_apply.returncode == 0

    def allowed_command(self, cmd: str) -> bool:
        cmd_clean = cmd.strip()
        for block in COMMAND_BLOCKLIST_PREFIXES:
            if cmd_clean.startswith(block):
                return False
        for allow in COMMAND_ALLOWLIST_PREFIXES:
            if cmd_clean.startswith(allow):
                return True
        return False
