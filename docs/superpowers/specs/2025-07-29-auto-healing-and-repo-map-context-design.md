# Design Spec: Auto-Healing, Context Repo-Map, and TUI Auto-Completer

## Overview
Enhance `agent-forge` with self-debugging / auto-healing capabilities (feeding test failures directly back to the tool agent loop), automatic repo symbol mapping in the context assembler, and slash command auto-completion in the interactive TUI.

---

## Architectural Enhancements

### 1. Slash Command Auto-Completer (`agent/cli/tui.py`)
- Implement `WordCompleter` from `prompt_toolkit.completion` containing `/plan`, `/status`, `/compact`, `/clear`, `/help`, `/exit`, `/quit`.
- Attach completer to `PromptSession` in `run_tui_loop()`.

### 2. Repo-Map Context Integration (`agent/runtime/context.py`)
- Integrate `generate_repo_map(project_dir)` into `build_context()` as a prioritized section.
- Ensures Gemini 2.5 Pro receives a clear, structural skeleton of all classes, functions, and methods across the project.

### 3. Auto-Healing Test Failure Loop (`agent/runtime/scheduler.py`)
- When `validate()` detects test failures, pass the exact `pytest` error output back into `run_tool_agent()` on retry attempts.
- Allows the agent to inspect the failure, locate the failing test/code line, and edit the file to fix the bug autonomously.

---

## Data Flow
```
User Request ("Fix test failure in user_auth.py")
  │
  ▼
Context Assembler (Includes Repo Symbol Map)
  │
  ▼
Tool Agent Loop (Edits file & runs bash)
  │
  ▼
Validator (Runs pytest) ───[ Fails ]───► Retries Tool Agent with Error Trace
  │                                           │
  └───[ Passes ]───► Git Checkpoint Commit ◄──┘
```

---

## Verification
- Unit tests for slash command completion.
- Unit tests for `build_context()` containing repo symbol map.
- Unit tests for auto-healing test failure loop in `scheduler.py`.
