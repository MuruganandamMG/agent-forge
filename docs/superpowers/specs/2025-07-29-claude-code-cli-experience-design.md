# Design Spec: Claude Code / Codex CLI Autonomous Experience

## Overview
Transform `agent-forge` into a fully autonomous, tool-driven CLI agent matching Claude Code and Codex CLI. The agent will operate via an iterative tool loop (`read_file`, `edit_file`, `write_file`, `search`, `list_dir`, `bash`), directly inspecting files, making precise edits, executing terminal commands, evaluating output, and self-correcting errors.

---

## Architectural Changes

### 1. Scheduler Core (`agent/runtime/scheduler.py`)
- Transition default task execution from raw git diff parsing to `run_tool_agent()`.
- Equip the tool agent with the full standard tool suite (`read_file`, `edit_file`, `write_file`, `search`, `list_dir`, `bash`).
- Maintain auto-commit sandbox checkpoints upon successful validation.

### 2. Live Tool Call Terminal Rendering (`agent/runtime/ui.py` & `agent/runtime/subagents/tool_agent.py`)
- Render live tool execution cards in terminal as the model calls them:
  - `🛠️ Tool: read_file -> path='agent/runtime/main.py'`
  - `🛠️ Tool: edit_file -> path='agent/runtime/main.py'`
  - `🛠️ Tool: bash -> command='pytest'`
- Render tool results inline with syntax formatting and error highlighting.

### 3. Integrated CLI Workflows (`agent/cli/run.py` & `agent/cli/chat.py`)
- Ensure both non-interactive single command execution (`agent run "<task>"`) and interactive REPL session (`agent chat`) execute via the autonomous tool agent engine.

---

## Data Flow
```
User Input ("Fix bug in main.py")
  │
  ▼
Classifier Gate -> Enricher -> Tool Agent Loop
  │
  ├─> Model calls `read_file` -> Execute -> Return file text to Model
  ├─> Model calls `search` -> Execute -> Return match results to Model
  ├─> Model calls `edit_file` -> Execute -> Return edit status to Model
  ├─> Model calls `bash("pytest")` -> Execute -> Return test stdout/stderr to Model
  │
  ▼
Validation Check -> Git Checkpoint Commit -> Output Session Summary
```

---

## Verification Plan
1. Unit tests for tool agent execution with real file/shell tools.
2. End-to-end integration tests verifying `run_agent()` executing tasks via tool calls and committing changes.
