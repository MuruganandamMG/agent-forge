# AGENTS.md

## Project Overview
This project is **`agent-forge`**, a **Git-native CLI autonomous coding agent** built with **Python**, **pytest**, and **Gemini Models** (Google GenAI SDK). It executes complex software engineering tasks directly in terminal and repository environments through multi-step planning, automated git diff sandboxing, test-driven validation, reviewer subagent critique, and persistent session management.

---

## Architecture & Codebase Map

The project is structured into `agent/cli/` (user interface layer) and `agent/runtime/` (execution engine):

### CLI User Interface (`agent/cli/`)
- `chat.py`: Interactive REPL session (`agent chat`). Handles conversation loops, `/plan` commands, and chat history.
- `run.py`: Single-task execution entry point (`agent run "<task>"`).
- `status.py`: Session status, pending tasks, and repository progress display (`agent status`).
- `config.py`: Agent configuration settings manager (`agent config`).

### Core Runtime Components (`agent/runtime/`)
- `main.py`: Primary Click CLI command group definitions and entry point routing.
- `gate.py`: Dual-stage safety gate (regex + LLM classifier) categorizing user input into `TASK`, `VAGUE`, or `CHAT`.
- `scheduler.py`: Central orchestration engine executing the 7-stage task pipeline:
  `Gate -> Enricher -> Planner -> Implementer -> Sandbox Diff -> Validator -> Reviewer -> Commit`.
- `subagents/`:
  - `core.py`: Specialized subagent dispatch routines (`run_planner`, `run_implementer`, `run_reviewer`).
  - `prompts.py`: System prompts governing subagent behavior and outputs.
- `providers/`:
  - `base.py`: Abstract LLM provider interface (`BaseProvider`).
  - `gemini_provider.py`: Google GenAI SDK integration targeting `gemini-2.5-pro`.
- `models.py`: Model provider factory and token counting abstraction.
- `sandbox.py`: Git sandbox environment manager executing diff application and checkpoint commits.
- `validate.py`: Quality control and automated `pytest` test runner.
- `context.py` & `indexer.py`: Workspace directory scanning, file indexing, token budgeting, and prompt assembly.
- `memory.py`: Vector database memory interface powered by ChromaDB.
- `session_state.py`: Session persistence manager maintaining state in `.agent_session.json`.
- `task_graph.py`: Task DAG parser and state graph tracker.
- `enricher.py` & `chat_responder.py`: Conversational context enrichment and chat response routines.
- `ui.py`: Rich console formatting, progress spinners, banners, and panels.

---

## Research & Documentation

Comprehensive architectural research, competitor analysis, and future engineering roadmaps are available in the `research/` directory:
- [`research/01_cli_agents_landscape_and_architecture.md`](research/01_cli_agents_landscape_and_architecture.md): Industry survey of Claude Code, Pi, Aider, Codex, and OpenHands, detailing the 6 architectural pillars of CLI agents.
- [`research/02_agent_forge_codebase_deep_analysis.md`](research/02_agent_forge_codebase_deep_analysis.md): Module-by-module breakdown of `agent-forge` runtime, execution pipelines, strengths, and limitations.
- [`research/03_gap_analysis_and_implementation_roadmap.md`](research/03_gap_analysis_and_implementation_roadmap.md): Feature gap matrix vs industry benchmarks and 5-phase implementation roadmap.

---

## Git Workflow & Branching Strategy
- **Never Push Directly to `main`**: All features, fixes, and refactors must happen on a dedicated branch (e.g., `feat/<name>`, `fix/<name>`).
- **Cloud Synchronization**: Always push local branches to the remote GitHub repository (`git push -u origin <branch-name>`). Do not keep branches local-only.
- **Pull Requests**: Once work is completed and verified on the branch, push to remote and use a Pull Request to merge into `main`.

---

## Coding & Patch Standards
- **Git Diffs**: Always generate and parse patches using standard unified git diff format (`diff -u` / `git diff`).
- **Clean Code**: Keep implementation concise, modular, readable, and maintain high cohesion with zero unnecessary fluff or boilerplate.
- **No Swallowed Errors**: Handle errors explicitly without masking runtime exceptions.

---

## Testing Guidelines
- **Framework**: Use `pytest` for test suites and validation.
- **Verification**: Run `pytest` to verify changes before marking tasks as complete.
- **Coverage**: Ensure key runtime components (`gate.py`, `context.py`, `sandbox.py`, `scheduler.py`, `subagents`, etc.) have test cases verifying core logic.
