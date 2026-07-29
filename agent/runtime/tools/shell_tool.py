import subprocess
from typing import Optional
from runtime.tools.base import ToolResult, tool

MAX_LINES = 2000
MAX_BYTES = 50 * 1024  # 50 KB

@tool(description="Execute a shell command in the repository workspace.")
def bash(command: str, timeout: int = 60) -> ToolResult:
    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )

        stdout = process.stdout or ""
        stderr = process.stderr or ""
        output = (stdout + ("\nSTDERR:\n" + stderr if stderr else "")).strip()

        # Truncate output if exceeding line or byte budget
        lines = output.splitlines()
        if len(lines) > MAX_LINES:
            lines = lines[-MAX_LINES:]
            output = f"[Truncated to last {MAX_LINES} lines]\n" + "\n".join(lines)

        if len(output.encode("utf-8")) > MAX_BYTES:
            output = output[-MAX_BYTES:]
            output = f"[Truncated to last {MAX_BYTES} bytes]\n" + output

        if process.returncode != 0:
            return ToolResult(
                success=False,
                output=output,
                error=f"Command exited with return code {process.returncode}"
            )

        return ToolResult(success=True, output=output if output else "Command executed successfully with no output.")

    except subprocess.TimeoutExpired:
        return ToolResult(
            success=False,
            output="",
            error=f"Command '{command}' timed out after {timeout} seconds."
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))
