# Implementation Plan: Sub-Project 4 (Interactive TUI with `prompt_toolkit`)

This plan details the implementation of an enhanced interactive TUI session with slash commands, history management, and Rich streaming output for `agent-forge`.

---

## Proposed Plan

### Task 1: Slash Command Parser & TUI Handler (`agent/cli/tui.py`)
- **Files**:
  - `agent/cli/tui.py`
  - `agent/tests/test_tui.py`
- **Implementation**:
  - Implement `SlashCommand` handler supporting `/plan`, `/status`, `/compact`, `/clear`, `/help`, `/exit`.
  - Implement `run_tui_loop()` using `prompt_toolkit.PromptSession` with history and keybindings.
- **Verification**:
  - Run `pytest agent/tests/test_tui.py`.

### Task 2: CLI Chat Command Integration (`agent/cli/chat.py`)
- **Files**:
  - `agent/cli/chat.py`
  - `agent/tests/test_cli_chat_tui.py`
- **Implementation**:
  - Connect `run_tui_loop` to `agent chat` entry point.
- **Verification**:
  - Run `pytest agent/tests/test_cli_chat_tui.py`.

---

## Final Verification Checklist
- Run `pytest agent/tests/test_tui.py agent/tests/test_cli_chat_tui.py`.
- Verify git status clean and commit changes.
