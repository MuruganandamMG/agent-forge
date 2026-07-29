# Implementation Plan: Sub-Project 2 (Live Shell Execution - `bash` Tool)

This plan details the implementation of a safe, live shell execution tool (`bash`) with timeouts, security checks, and output truncation for `agent-forge`.

---

## Proposed Plan

### Task 1: Shell Execution Tool (`agent/runtime/tools/shell_tool.py`)
- **Files**:
  - `agent/runtime/tools/shell_tool.py`
  - `agent/tests/test_shell_tool.py`
- **Implementation**:
  - Implement `bash(command: str, timeout: int = 60) -> ToolResult`.
  - Add execution timeout support (raises error / returns failure if command exceeds limit).
  - Add stdout/stderr truncation (max 2000 lines / 50KB).
  - Integrate with `tool_registry`.
- **Verification**:
  - Run `pytest agent/tests/test_shell_tool.py`.

### Task 2: Tool Agent & Scheduler Shell Integration
- **Files**:
  - `agent/runtime/tools/__init__.py`
  - `agent/tests/test_tool_agent_shell.py`
- **Implementation**:
  - Export `bash` tool in `runtime/tools/__init__.py`.
  - Verify `run_tool_agent` can execute `bash` commands in loop.
- **Verification**:
  - Run `pytest agent/tests/test_tool_agent_shell.py`.

---

## Final Verification Checklist
- Run `pytest agent/tests/test_shell_tool.py agent/tests/test_tool_agent_shell.py`.
- Verify git status clean and commit changes.
