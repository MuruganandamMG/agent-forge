# Implementation Plan: Sub-Project 1 (Native Tool-Calling Framework)

This plan details the implementation of a native tool-calling framework for `agent-forge` using Google GenAI SDK (`gemini-2.5-pro`) and standard file operations tools (`read_file`, `edit_file`, `write_file`, `search`, `list_dir`).

---

## User Review Checkpoints

> [!NOTE]
> Implementation will be conducted step by step using Test-Driven Development (TDD).

---

## Proposed Plan

### Task 1: Tool Registry & Base Declarations (`agent/runtime/tools/base.py`)
- **Files**:
  - `agent/runtime/tools/base.py`
  - `agent/tests/test_tools_base.py`
- **Implementation**:
  - Create `@tool` decorator or `Tool` base class converting Python functions into `types.FunctionDeclaration` / `types.Tool`.
  - Define `ToolResult` dataclass (`success: bool`, `output: str`, `error: str | None`).
- **Verification**:
  - Run `pytest agent/tests/test_tools_base.py`.

### Task 2: File System Tools (`agent/runtime/tools/file_tools.py`)
- **Files**:
  - `agent/runtime/tools/file_tools.py`
  - `agent/tests/test_file_tools.py`
- **Implementation**:
  - Implement `read_file(path, offset=1, limit=2000)`
  - Implement `edit_file(path, old_text, new_text)`
  - Implement `write_file(path, content)`
  - Implement `search(query, path=".")`
  - Implement `list_dir(path=".")`
- **Verification**:
  - Run `pytest agent/tests/test_file_tools.py`.

### Task 3: Gemini Provider Function Calling Support (`agent/runtime/providers/gemini_provider.py`)
- **Files**:
  - `agent/runtime/providers/gemini_provider.py`
  - `agent/tests/test_gemini_provider_tools.py`
- **Implementation**:
  - Update `GeminiProvider.chat()` to accept optional `tools` parameter and return both response text and function call requests.
  - Implement helper to format tool results into `types.Content` with function response parts.
- **Verification**:
  - Run `pytest agent/tests/test_gemini_provider_tools.py`.

### Task 4: Tool Execution Loop & Implementer Subagent Integration (`agent/runtime/subagents/tool_agent.py`)
- **Files**:
  - `agent/runtime/subagents/tool_agent.py`
  - `agent/tests/test_tool_agent.py`
- **Implementation**:
  - Implement `run_tool_agent(task, tools, max_turns=10)` loop.
  - Integrate tool loop into `run_implementer()` as primary tool-based execution strategy.
- **Verification**:
  - Run `pytest agent/tests/test_tool_agent.py`.

---

## Final Verification Checklist
- Run `pytest agent/tests/` (with `GEMINI_API_KEY=dummy_key` for offline test mocks).
- Verify git status clean and commit changes.
