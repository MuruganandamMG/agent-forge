import re
import subprocess
from collections.abc import Callable
from pathlib import Path


def read_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
    """Read contents of a file, optionally restricted to a line range (1-indexed)."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    content = p.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines(keepends=True)

    start_idx = max(0, start_line - 1)
    if end_line is not None:
        selected_lines = lines[start_idx:end_line]
    else:
        selected_lines = lines[start_idx:]

    return "".join(selected_lines)


def list_dir(path: str) -> list[dict]:
    """List directory contents with name, is_dir, and size metadata."""
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    items = []
    for item in sorted(p.iterdir(), key=lambda x: x.name):
        is_dir = item.is_dir()
        size = item.stat().st_size if item.is_file() else None
        items.append({"name": item.name, "is_dir": is_dir, "size": size})

    return items


def grep_search(pattern: str, path: str, case_insensitive: bool = False) -> list[dict]:
    """Search files for a regex pattern, returning matching lines capped at 50 results."""
    p = Path(path)
    flags = re.IGNORECASE if case_insensitive else 0
    regex = re.compile(pattern, flags)

    if p.is_file():
        files = [p]
    elif p.is_dir():
        files = [f for f in sorted(p.rglob("*")) if f.is_file()]
    else:
        return []

    results = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        lines = text.splitlines()
        for line_idx, line in enumerate(lines, start=1):
            if regex.search(line):
                results.append({
                    "file": str(f),
                    "line": line_idx,
                    "content": line,
                })
                if len(results) >= 50:
                    return results

    return results


def run_command(cmd: str, cwd: str | None = None, timeout: int = 30) -> dict:
    """Run a shell command, returning returncode, stdout, and stderr."""
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return {
            "returncode": proc.returncode,
            "stdout": stdout if stdout is not None else "",
            "stderr": stderr if stderr is not None else "",
        }
    except subprocess.TimeoutExpired:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
            )
        except Exception:
            pass
        proc.kill()
        proc.communicate()
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }


TOOLS: dict[str, Callable] = {
    "read_file": read_file,
    "list_dir": list_dir,
    "grep_search": grep_search,
    "run_command": run_command,
}
