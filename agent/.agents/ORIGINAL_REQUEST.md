# Original User Request

## Initial Request — 2026-07-24T17:14:31Z

Build a local CLI agentic coding assistant with explicit `/plan` multi-step planning mode and direct single-task execution mode, running on Windows with an 8GB VRAM budget.

Working directory: E:\AI\Models\Agentic AI's in CLI\agent
Integrity mode: development

## Requirements

### R1. Command-Triggered Multi-Step Planning (`/plan`)
The agent must execute direct single-task execution by default when user inputs requests. Only when the input is explicitly prefixed with `/plan` (or `/plan <request>`) should the multi-step JSON planner module be invoked.

### R2. Direct Execution Mode
In direct execution mode (without `/plan`), the agent must immediately execute the request as a single code generation task through the executor and validation pipeline without multi-step planner overhead.

### R3. Clarification Task Branching
If a task type is `clarify` (or task description starts with `CLARIFY:`), the agent must prompt the user directly for clarification and store the answer in memory without attempting patch generation or validation.

### R4. Automated Quality Gate & Security Sandbox
All generated diffs must pass `black`, `ruff`, and `pytest` validation before human approval. Hardened git sandbox must enforce command blocklisting (`rm`, `del`, `curl`, `powershell`) and allowlisting (`python`, `pytest`, `black`, `ruff`, `git`).

## Acceptance Criteria

### Execution & Command Handling
- [x] Typing `you> create a module` runs direct single-task execution without planner overhead
- [x] Typing `you> /plan create a full module with tests` invokes multi-step planner
- [x] Tasks of type `clarify` prompt user for input directly
- [x] All 63 unit and integration tests pass cleanly (`pytest tests/`)
- [x] Server auto-locates `llama-server.exe` and offloads all layers (`-ngl 99`)
