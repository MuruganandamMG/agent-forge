# Codebase Deep Analysis: agent-forge

## Executive Summary

`agent-forge` is a Git-native autonomous CLI coding agent implemented in Python. It provides a task execution runtime combining multi-step planning, subagent delegation, automated git diff application, sandbox test validation (`pytest`), and session state tracking.

This document provides a comprehensive structural analysis of the codebase, detailing its component architecture, data flow pipelines, implementation patterns, key strengths, technical debt, and architectural limitations.

---

## 1. System Directory & Module Inventory

```
agent-forge/
├── main.py                          # Top-level entry point delegating to agent.runtime.main
├── agent/
│   ├── cli/                         # CLI User Interface Layer
│   │   ├── chat.py                  # Interactive REPL session ('agent chat')
│   │   ├── run.py                   # Single task execution mode ('agent run')
│   │   ├── status.py                # Session status display ('agent status')
│   │   └── config.py                # Configuration management ('agent config')
│   ├── runtime/                     # Core Agent Orchestration Runtime
│   │   ├── main.py                  # Click CLI group definitions
│   │   ├── gate.py                  # Dual-stage input classifier (Regex + LLM)
│   │   ├── scheduler.py             # Main execution orchestrator (Planner -> Exec -> Test -> Reviewer)
│   │   ├── context.py               # Token budgeting & prompt context assembler
│   │   ├── indexer.py               # Project file tree scanner & system context generator
│   │   ├── filetree.py              # Directory tree formatting helper
│   │   ├── memory.py                # Vector memory interface (ChromaDB)
│   │   ├── sandbox.py               # Git sandbox environment & diff application
│   │   ├── validate.py              # Local code quality & pytest validation harness
│   │   ├── session_state.py         # Session persistence & chat history tracker (.agent_session.json)
│   │   ├── enricher.py              # Request context enricher
│   │   ├── ui.py                    # Rich terminal UI utilities (spinners, banners, panels)
│   │   ├── task_graph.py            # Task DAG & state graph management
│   │   ├── chat_responder.py        # Conversational chat response generator
│   │   ├── models.py                # Provider selection factory & token counter
│   │   ├── providers/               # LLM Provider Drivers
│   │   │   ├── base.py              # Abstract BaseProvider interface
│   │   │   └── gemini_provider.py   # Google GenAI SDK integration (Gemini 2.5 Pro)
│   │   └── subagents/               # Specialized Agent Subroutines
│   │       ├── core.py              # Subagent invocation functions (run_planner, run_implementer, run_reviewer)
│   │       └── prompts.py           # System prompts for Planner, Implementer, Reviewer
│   └── prompts/                     # Global System Prompt Templates
│       ├── classifier_system.txt    # Input gate classification prompt
│       ├── executor_system.txt      # Code implementer prompt
│       └── planner_system.txt       # Task graph planner prompt
```

---

## 2. Core Execution Pipeline & Data Flow

The lifecycle of a user task in `agent-forge` follows a structured 7-stage pipeline:

```
[User Input] 
     │
     ▼
[Stage 1: Gate Classifier (gate.py)] ──(Trivial/Chat)──> [chat_responder.py] ──> [Terminal Output]
     │
     ▼ (Task Input)
[Stage 2: Context Indexing & Enrichment (indexer.py, enricher.py)]
     │
     ▼
[Stage 3: Multi-Step Planner (scheduler.py, subagents/core.py)] ──> Builds [TaskGraph]
     │
     ▼
[Stage 4: Code Generation / Implementer Subagent (subagents/core.py)]
     │
     ▼
[Stage 5: Sandbox Diff Application (sandbox.py)]
     │ (Git Diff Apply)
     ├── (Fail: Diff syntax / line shift) ──> Retry with Feedback (Max 3 attempts)
     ▼ (Success)
[Stage 6: Automated Validation (validate.py)]
     │ (Pytest Execution)
     ├── (Fail: Test failure) ─────────────> Revert Git Checkout & Retry with Feedback
     ▼ (Success)
[Stage 7: Reviewer Subagent Gate (subagents/core.py)]
     │
     ├── (Reject: Changes requested) ──────> Revert Git Checkout & Retry with Feedback
     ▼ (APPROVED)
[Git Checkpoint Commit & Session State Persistence (session_state.py)]
```

### Detailed Pipeline Breakdown:

1. **Input Gate Classification (`gate.py`)**:
   - Fast regex match (`quick_classify`) checks for short greetings, gibberish, or clear code keywords.
   - Stage 2 LLM call (`llm_classify`) evaluates ambiguous prompts as `TASK`, `VAGUE`, or `CHAT`.

2. **Project Indexing (`indexer.py`)**:
   - Traverses workspace (respecting `.gitignore`), building a formatted string representation of file trees and file paths.

3. **Planning Stage (`scheduler.py`)**:
   - If `/plan` is invoked, calls `run_planner` to generate a JSON array of tasks, parsed into a `TaskGraph`.
   - In direct mode, creates a single-task `TaskGraph`.

4. **Implementation Subagent (`subagents/core.py`)**:
   - Reads content of files referenced in task.
   - Invocates `run_implementer` with instructions, code context, and prior retry feedback.
   - Returns a standard unified git diff string (`diff -u`).

5. **Sandbox Diff Application (`sandbox.py`)**:
   - Initializes git repo in sandbox workspace if needed.
   - Attempts `git apply` on the generated patch.

6. **Local Test Validation (`validate.py`)**:
   - Runs `pytest` in the sandbox environment.
   - Captures stdout/stderr. If tests fail, automatically executes `git checkout .` to revert dirty state, passing test error logs back to the Implementer subagent for retry (up to `MAX_RETRIES = 3`).

7. **Reviewer Subagent Gate (`subagents/core.py`)**:
   - Evaluates the proposed diff against task requirements.
   - Returns `"APPROVED"` or detailed critique feedback.
   - Upon approval, creates a clean git commit checkpoint.

---

## 3. Detailed Component Analysis

### 3.1 LLM Provider Architecture (`providers/`, `models.py`)
- **Current State**: Uses Google's official `google-genai` SDK (`GeminiProvider`) targeted at `gemini-2.5-pro`.
- **Interface**: Implements `BaseProvider` (`chat`, `count_tokens`).
- **Limitation**: Uses heuristic token counting (`len(text) // 4`). Model provider is hardcoded to Gemini; no native Anthropic Claude or OpenAI support implemented yet.

### 3.2 Subagent Framework (`subagents/`)
- **Current State**: Three distinct subagents: `Planner`, `Implementer`, and `Reviewer`.
- **Implementation**: Structured around simple function calls returning strings.
- **Strength**: Clean separation of roles. Reviewer subagent acts as an effective critique filter before committing code.

### 3.3 Context Management & Memory (`context.py`, `memory.py`, `indexer.py`)
- **Current State**: Assembles prompts with file tree, `AGENTS.md` contents, memory context, and relevant code files.
- **Memory**: Persistent ChromaDB vector database (`Memory` class) storing past query/response sessions and reflections.
- **Limitation**: Context window allocation is based on fixed string concatenation budgets without dynamic AST symbol extraction or smart context compaction.

### 3.4 Terminal UI & CLI (`cli/`, `ui.py`)
- **Current State**: Powered by `click` and `rich`. Provides colored console output, Markdown rendering, banners, and status spinners.
- **Limitation**: Lacks interactive prompt history (`prompt_toolkit`), live streaming tool output, and slash-command autocompletion.

---

## 4. Codebase Strengths & Architectural Limitations

### Core Strengths
1. **Automated Test Feedback Loop**: Hard requirement for `pytest` passing before code approval ensures working code output.
2. **Reviewer Critique Subagent**: Secondary LLM evaluation prevents trivial bugs, syntax errors, or missed requirements.
3. **Git Sandbox Safety**: Automatic git rollbacks (`git checkout .`) on failed attempts prevent workspace corruption.
4. **Persistent Session State**: `.agent_session.json` preserves multi-turn conversation and task context across restarts.

### Architectural Limitations & Technical Debt
1. **Lack of Direct Tool Calling / Function Calling**: Agent relies on asking LLM to emit raw unified diffs in text format rather than invoking structured tools (`read_file`, `bash`, `edit_file`).
2. **Non-Streaming Terminal Execution**: CLI waits for full model responses before displaying output, impacting perceived user latency.
3. **Simplistic Token Heuristic**: Character division (`len // 4`) can lead to token overflow on code-heavy or multibyte responses.
4. **No Live Shell Execution Tool**: The agent cannot execute arbitrary bash commands (e.g., `pip install`, `npm build`, `grep`) during the agentic loop.
