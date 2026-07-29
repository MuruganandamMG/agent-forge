# CLI Agent Research and Codebase Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Perform deep research into state-of-the-art CLI coding agents (Claude Code, OpenAI Codex, Pi, Aider, OpenHands), analyze the complete `agent-forge` codebase, create comprehensive markdown research documents in `research/`, and update `AGENTS.md`.

**Architecture:** Create a dedicated `research/` directory containing three granular, highly detailed markdown documents detailing industry paradigms, codebase architecture, gap analysis, and future roadmap. Update root `AGENTS.md` and `agent/AGENTS.md` to reflect full architectural context and research pointers.

**Tech Stack:** Markdown (`.md`), Git, Python runtime analysis.

## Global Constraints

- Research files must be saved in `research/` directory.
- `research/01_cli_agents_landscape_and_architecture.md` covers leading CLI agents, paradigms, context strategies, execution, editing, and safety.
- `research/02_agent_forge_codebase_deep_analysis.md` provides module-by-module breakdown of `agent-forge`.
- `research/03_gap_analysis_and_implementation_roadmap.md` provides gap matrix vs Claude Code/Pi/Aider and multi-phase implementation roadmap.
- `AGENTS.md` and `agent/AGENTS.md` must be updated with clear pointers to research and complete runtime architecture.

---

### Task 1: Research CLI Agents Landscape & Architecture Document

**Files:**
- Create: `research/01_cli_agents_landscape_and_architecture.md`

**Interfaces:**
- Produces: Industry standards and component specifications for CLI coding agents.

- [ ] **Step 1: Write `research/01_cli_agents_landscape_and_architecture.md`**

Write a deep-dive research document detailing:
1. Analysis of premier CLI agents (Claude Code, Pi Agent Harness, OpenAI Codex CLI, Aider, OpenHands/OpenDevin).
2. Key Architectural Pillars:
   - Interactive Shell / UX & Terminal Handling (Rich ANSI, streaming, spinners, prompt-toolkit, multiline input).
   - Tool Call & Execution Harness (MCP protocol, bash tools, file operations, output truncation & pagination).
   - Editing Paradigms (Unified Git diffs vs Search/Replace blocks vs Full file overwrites vs AST modification).
   - Context Management & Retrieval (Tree-sitter AST repo mapping, vector search, sliding context window, auto-compaction).
   - Agentic Control Loops & Subagent Delegation (Planner-Executor-Reviewer dynamics, multi-agent parallel execution).
   - Safety, Permissions & Gatekeeping (Risk classification, command auto-approval vs human-in-the-loop).

- [ ] **Step 2: Verify file creation and format**

Run: `ls -la research/01_cli_agents_landscape_and_architecture.md`

- [ ] **Step 3: Commit**

```bash
git add research/01_cli_agents_landscape_and_architecture.md
git commit -m "docs: add CLI agents landscape and architecture research"
```

---

### Task 2: Codebase Deep Analysis, Gap Matrix & Implementation Roadmap

**Files:**
- Create: `research/02_agent_forge_codebase_deep_analysis.md`
- Create: `research/03_gap_analysis_and_implementation_roadmap.md`

**Interfaces:**
- Consumes: Codebase state from `agent/runtime/` and `agent/cli/`.
- Produces: Exhaustive codebase inspection, strengths/weaknesses matrix, gap matrix vs industry benchmarks, and multi-phase roadmap.

- [ ] **Step 1: Write `research/02_agent_forge_codebase_deep_analysis.md`**

Write a complete analysis of `agent-forge`:
1. System Component Map: `main.py`, `agent/cli/` (`chat.py`, `run.py`, `status.py`, `config.py`), `agent/runtime/` (`gate.py`, `scheduler.py`, `context.py`, `sandbox.py`, `indexer.py`, `memory.py`, `subagents/`, `providers/`, `ui.py`, `validate.py`).
2. Data Flow & Execution Pipeline: Request Entry -> Gate Classifier -> Enricher -> Multi-step Planner -> Implementer Subagent -> Git Sandbox Diff -> Validation (`pytest`) -> Reviewer Subagent -> Commit & State Update.
3. Component Strengths & Weaknesses (e.g. Automated test validation & Reviewer gate strength vs missing tool-use function calling, static token heuristic, lack of live command streaming).

- [ ] **Step 2: Write `research/03_gap_analysis_and_implementation_roadmap.md`**

Write a feature gap matrix and roadmap:
1. Feature Gap Matrix: `agent-forge` vs Claude Code vs Pi vs Aider.
2. Implementation Roadmap:
   - Phase 1: Native Function Calling / Tool Specification (MCP integration).
   - Phase 2: Interactive Terminal Tools & Live Subprocess Streaming.
   - Phase 3: Tree-Sitter Repository Mapping & Smart Context Window Compaction.
   - Phase 4: Full TUI & Slash Commands (Prompt-Toolkit / Textual).
   - Phase 5: Multi-Provider LLM Engine (Anthropic, OpenAI, Local Ollama/llama.cpp).

- [ ] **Step 3: Verify files created**

Run: `ls -la research/`

- [ ] **Step 4: Commit**

```bash
git add research/
git commit -m "docs: add codebase deep analysis, gap matrix, and implementation roadmap"
```

---

### Task 3: Update AGENTS.md Documentation & Verification

**Files:**
- Modify: `AGENTS.md`
- Modify: `agent/AGENTS.md`

**Interfaces:**
- Consumes: Research insights and updated architecture details.
- Produces: Up-to-date documentation for agents working on this project.

- [ ] **Step 1: Update `AGENTS.md` and `agent/AGENTS.md`**

Incorporate full system architectural map, provider & subagent breakdown, research folder references, git workflow guidelines, and testing requirements.

- [ ] **Step 2: Run verification checks**

Check that pytest passes and all markdown files are correctly positioned.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md agent/AGENTS.md
git commit -m "docs: update AGENTS.md with architecture and research pointers"
```
