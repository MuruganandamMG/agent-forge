# CLI Modernization and Pruning Design

## Overview
The goal is to modernize the CLI experience to match professional tools like `claude` or `pi` CLI. This involves completely ripping out legacy local-server logic (`llama-server`) that is no longer used now that the agent is powered directly by the Gemini API via the `google.genai` SDK.

## Components to Update

### 1. `agent/runtime/main.py`
- Remove all `llama-server` specific options (`--port`, `--ctx-size`, `--server-bin`).
- Keep `--project` and `--model`.
- Remove the passing of legacy variables into the `click.Context` (`ctx.obj`).

### 2. `agent/cli/chat.py` & `agent/cli/run.py`
- Remove the extraction of `port`, `ctx_size`, and `server_bin` from `ctx.obj`.
- Remove the call to `health_check()` and the "assuming model server is running" echo statements.
- Polish the CLI output banner to be cleaner and more unified.
  - E.g., `⚡ Forge Agent | Model: gemini-2.5-pro | Project: <path>`
  - Merge the indexing output to be concise.

### 3. `agent/runtime/models.py`
- Delete `health_check()` and `ensure_server()` completely as they are dead code and currently unused by the core agent flow.

### 4. Tests
- Update `tests/test_cli_main.py`, `tests/test_cli_chat.py`, `tests/test_cli_run.py`, and `tests/test_models.py` to remove any assertions or mocks related to `health_check`, `ensure_server`, `--port`, or `--ctx-size`.

## UX Polish
- Ensure standard output flows nicely without unnecessary line breaks or emoji clutter.
- The REPL prompt should remain `you>` for simplicity.

## Constraints
- Do not modify core execution logic (`scheduler.py`, `sandbox.py`, `context.py`). This is purely a CLI parsing and UX cleanup layer.
- Tests must pass after pruning.
