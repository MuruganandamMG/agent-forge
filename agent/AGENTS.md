# AGENTS.md

## Project Overview
This project is a **Git-native CLI coding agent** built with **Python**, **pytest**, and **llama-server**. It executes tasks in terminal/repo environments, managing diffs, sandbox execution, context resolution, and scheduling.

## Architectural Layout
The core agent logic is structured inside `agent/runtime/`:

- `main.py`: Entry point and primary event/command loop for the CLI agent.
- `gate.py`: Safety gate and permissions checking layer before executing actions/commands.
- `filetree.py`: Workspace directory tree indexing, tracking, and structure discovery.
- `context.py`: Context window assembly, token management, prompt construction, and state tracking.
- `models.py`: LLM client integrations and communication handlers for `llama-server`.
- `sandbox.py`: Isolated environment execution for commands and safe evaluation.
- `validate.py`: Validation routines for outputs, edits, and structural sanity checks.
- `scheduler.py`: Task scheduling, async job coordination, and background execution management.

## Coding & Patch Standards
- **Git Diffs**: Always generate and parse patches using standard unified git diff format (`diff -u` / `git diff`).
- **Clean Code**: Keep implementation concise, modular, readable, and maintain high cohesion with zero unnecessary fluff or boilerplate.
- **No Swallowed Errors**: Handle errors explicitly without masking runtime exceptions.

## Testing Guidelines
- **Framework**: Use `pytest` for test suites and validation.
- **Verification**: Run `pytest` to verify changes before marking tasks as complete.
- **Coverage**: Ensure key runtime components (`gate.py`, `context.py`, `sandbox.py`, etc.) have test cases verifying core logic.
