# CLI Coding Agent System Design

## Overview
Transform the existing single-entry `main.py` CLI script into a comprehensive, modular multi-command CLI using Python's `click` framework. This will provide a professional interface with subcommands for chat, batch execution, configuration, and status reporting.

## Architecture & Components

The system introduces a new `agent/cli/` module to handle subcommand routing, keeping the `agent/runtime/` core focused on execution logic.

### 1. File Structure
```
agent/
├── cli/
│   ├── __init__.py
│   ├── chat.py       # Interactive REPL mode
│   ├── run.py        # Single-shot query or file execution
│   ├── config.py     # Local workspace config management
│   └── status.py     # Session state and history reporting
└── runtime/
    ├── main.py       # Refactored into a @click.group() root
    └── ...
```

### 2. Root Command (`agent/runtime/main.py`)
- Becomes a `@click.group(invoke_without_command=False)`.
- Accepts global options: `--project` and `--model`.
- Initializes the environment: resolves paths, loads `.env` or config files, and prepares the `click.Context` (`ctx.obj`) so subcommands can inherit `project_dir` and `model`.

### 3. Subcommands

#### `chat` (Interactive Mode)
- **Command:** `agent chat`
- **Behavior:** Houses the `while True` loop currently in `main.py`.
- **Flow:** Indexes the project (via `generate_project_context`), loads `session_state`, and loops for user input. Calls `run_agent()` and updates session state on every turn.

#### `run` (Batch/Single-Shot Mode)
- **Command:** `agent run <query_or_file>`
- **Behavior:** Executes a task and exits.
- **Flow:** 
  - If the argument is an existing file (e.g., `plan.md`), it reads the contents and passes them as the prompt.
  - If it's a string, it passes it directly.
  - Indexes project once, calls `run_agent()`, updates session state, and exits.

#### `status` (Session Reporting)
- **Command:** `agent status`
- **Behavior:** Reads `session_state.json` via `session_state.py`.
- **Flow:** Prints the `last_goal`, lists `completed_tasks`, lists `pending_tasks`, and highlights `open_errors` cleanly to the console.

#### `config` (Settings Management)
- **Command:** `agent config [set|get|list] <key> <value>`
- **Behavior:** Reads/writes to a standard configuration file (e.g., `agent/.agents` or `.superpowers/config.json`) so the user doesn't have to specify `--model` every time.

## Data Flow & Constraints
- **State passing:** `click.pass_context` ensures subcommands don't re-parse global arguments.
- **Index caching:** Project indexing happens *inside* the subcommands (`chat` and `run`) rather than at the root group level, ensuring `status` and `config` commands run instantly without indexing overhead.
- **Error Handling:** All CLI errors will be caught and raised as `click.ClickException` or handled gracefully without swallowing stack traces per `AGENTS.md`.
