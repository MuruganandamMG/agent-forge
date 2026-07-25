# Project: Local CLI Agentic Coding Assistant

## Architecture
Local CLI agentic coding assistant running on Windows with an 8GB VRAM budget.
Core modules in `runtime/`, `prompts/`, and test suite in `tests/`.

## Requirements Summary
- R1: Command-Triggered Multi-Step Planning (/plan)
- R2: Direct Execution Mode (without /plan, single task execution without planner overhead)
- R3: Clarification Task Branching (task type 'clarify' or starting with 'CLARIFY:' prompts user directly and updates memory without patch generation/validation)
- R4: Automated Quality Gate & Security Sandbox (black, ruff, pytest validation; hardened git sandbox command blocklist [rm, del, curl, powershell] and allowlist [python, pytest, black, ruff, git])
- Acceptance Criteria:
  * typing `you> create a module` runs direct single-task execution without planner overhead
  * typing `you> /plan create a full module with tests` invokes multi-step planner
  * Tasks of type `clarify` prompt user for input directly
  * All 63 unit and integration tests pass cleanly (`pytest tests/`)
  * Server auto-locates `llama-server.exe` and offloads all layers (`-ngl 99`)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Baseline Analysis | Investigate codebase, test suite, and identify gaps | none | DONE |
| 2 | Implementation of R1 & R2 | Command-triggered /plan and Direct Execution mode | M1 | DONE |
| 3 | Implementation of R3 & R4 | Clarification task branching & Quality/Sandbox gates | M1 | DONE |
| 4 | Test Verification & Hardening | Ensure all 63 unit and integration tests pass | M2, M3 | DONE |

## Code Layout
- `runtime/`: CLI, model server integration, planner, executor, sandbox, memory modules.
- `prompts/`: System prompts for planning, code generation, clarification.
- `tests/`: 63 unit and integration tests.
