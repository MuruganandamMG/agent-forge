# CLI Entrypoint & Main.py Specification

**Date:** 2025-07-26
**Goal:** Enable seamless execution of the `agent` CLI globally (`agent chat`, `agent run`, `agent status`, `agent config`) and update `agent/runtime/main.py` with version flags, API key validation, and setup scripts.

## 1. Overview
Currently, `agent/pyproject.toml` lacks a `[project.scripts]` entry, requiring long `PYTHONPATH=agent python -m runtime.main ...` commands.
This spec updates `pyproject.toml` to register `agent = "runtime.main:main"` and updates `agent/runtime/main.py` with:
- `agent --version` / `agent -v`
- API Key check (`GEMINI_API_KEY`) with user-friendly error guidance if missing
- Editable installation support (`pip install -e agent`)

## 2. File Changes
1. `agent/pyproject.toml`:
   - Add `[project.scripts]` -> `agent = "runtime.main:main"`
2. `agent/runtime/main.py`:
   - Add `--version` flag (`0.1.0`).
   - Validate `GEMINI_API_KEY` before command execution.
   - Show helpful usage guide if invoked without subcommands.

## 3. Verification
- Run `pip install -e agent`
- Verify `agent --help`, `agent --version`, `agent status`, `agent chat --help`, `agent run --help` work directly in terminal.
