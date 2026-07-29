# Gap Analysis & Implementation Roadmap: agent-forge

## Executive Summary

To elevate `agent-forge` from a diff-generation agent into a premier autonomous CLI software engineering assistant comparable to **Claude Code**, **Pi**, and **Aider**, key architectural gaps must be addressed.

This document details the feature gap matrix between `agent-forge` and industry benchmarks, followed by a multi-phase implementation roadmap.

---

## 1. Feature Gap Analysis Matrix

| Feature Area | Claude Code | Pi Agent Harness | Aider | **agent-forge (Current)** | **Gap Level** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tool Execution Protocol** | Native Tool Call / MCP | Custom Tools / Extensions | Function Calling / Edit Block | Raw text diff parsing | 🔴 High Gap |
| **Terminal / Shell Execution** | Live streaming Bash tool | Native terminal tool | Interactive shell | Sandbox `pytest` runner only | 🔴 High Gap |
| **Code Editing Mechanism** | File replace / Patch | Precise File Edits | Search/Replace blocks | Unified Git Diff (`diff -u`) | 🟡 Moderate |
| **Codebase Mapping** | AST Symbol Graph / RAG | Workspace tree | cTags / Tree-Sitter Repo Map | Plain directory tree string | 🔴 High Gap |
| **Context Management** | Auto-compacting history | Token budget windowing | Minimal context sliding | Fixed string token budget | 🟡 Moderate |
| **Subagent Delegation** | Background agents | Multi-agent dispatch | Single agent mode | Planner-Implementer-Reviewer | 🟢 Low Gap |
| **Multi-Provider Support** | Anthropic Native + MCP | Multi-provider | Multi-provider (LiteLLM) | Gemini 2.5 Pro only | 🟡 Moderate |
| **Interactive UX** | Streaming, interrupt, TUI | Prompt templates, TUI | Streamed diffs, history | Rich spinners, no streaming | 🟡 Moderate |
| **Safety & Gatekeeping** | Risk classification gate | Permissions framework | Git commit sandbox | Regex + LLM classifier | 🟢 Low Gap |

---

## 2. Strategic Implementation Roadmap

```
+-----------------------------------------------------------------------+
| PHASE 1: Native Tool Framework & Function Calling                     |
| - Standardize tool call definitions (JSON Schema / Pydantic)          |
| - Implement read_file, edit_file, write_file, search_files tools     |
+-----------------------------------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------+
| PHASE 2: Native Shell Execution & Streaming Subprocess                |
| - Implement streaming `bash` tool with execution timeouts             |
| - Add output truncation (2000 lines / 50KB limit) & cancel interrupts |
+-----------------------------------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------+
| PHASE 3: Tree-Sitter Repository Mapping & Smart Context Compactor     |
| - Replace plain file tree with AST symbol repository map             |
| - Implement auto-summarizing context window compactor                 |
+-----------------------------------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------+
| PHASE 4: Interactive TUI, Streaming Response & Slash Commands         |
| - Integrate `prompt_toolkit` for history, multiline edit, auto-complete|
| - Implement live response streaming in `cli/chat.py`                  |
+-----------------------------------------------------------------------+
                                   │
                                   ▼
+-----------------------------------------------------------------------+
| PHASE 5: Multi-Provider Drivers & Model Agnostic Engine               |
| - Add Anthropic Claude 3.7 / 3.5 Sonnet provider                      |
| - Add OpenAI GPT-4o / Local Ollama provider support                   |
+-----------------------------------------------------------------------+
```

---

## 3. Detailed Phase Specifications

### Phase 1: Native Tool Framework (`runtime/tools.py`)
- **Objective**: Replace text-based diff generation with native LLM function/tool calls.
- **Components to Implement**:
  - `Tool` base class and decorator registry in `runtime/tools.py`.
  - Built-in tool specs:
    - `read_file(path, offset, limit)`
    - `edit_file(path, old_text, new_text)`
    - `write_file(path, content)`
    - `list_directory(path)`
    - `search_code(query, path)`
  - Update `GeminiProvider` to accept tool schemas and parse tool execution calls.

### Phase 2: Native Shell Execution & Terminal Tool (`runtime/sandbox.py`, `runtime/tools.py`)
- **Objective**: Grant the agent controlled bash command execution capabilities.
- **Components to Implement**:
  - `bash(command, timeout=30)` tool running inside sandbox environment.
  - Asynchronous subprocess streaming capturing stdout and stderr in real time.
  - Automatic output truncation (truncate long test outputs, keeping head and tail lines).
  - Safety filter verifying high-risk commands against `gate.py` permissions.

### Phase 3: Tree-Sitter Repository Mapping & Context Compactor (`runtime/indexer.py`, `runtime/context.py`)
- **Objective**: Provide deep codebase architectural understanding without context bloat.
- **Components to Implement**:
  - Integrate `tree-sitter` for Python, JavaScript, TypeScript, and Go parsing.
  - Generate a compact symbol map (class definitions, function signatures, docstrings).
  - Implement `ContextCompactor` in `context.py` that auto-summarizes earlier turns when history exceeds 70% of model context.

### Phase 4: Modern Interactive CLI UX (`cli/chat.py`, `runtime/ui.py`)
- **Objective**: Deliver a responsive terminal interface equal to Claude Code.
- **Components to Implement**:
  - Integrate `prompt_toolkit` in `cli/chat.py` for multiline input, persistent history (`~/.agent_history`), and keybindings.
  - Implement real-time token streaming in `ui.py`.
  - Add slash command system (`/plan`, `/compact`, `/clear`, `/model`, `/help`).

### Phase 5: Multi-Provider Abstraction Layer (`runtime/providers/`)
- **Objective**: Allow seamless swapping between Gemini, Anthropic Claude, OpenAI, and local models.
- **Components to Implement**:
  - `AnthropicProvider` (`anthropic` SDK integration for Claude 3.5/3.7 Sonnet).
  - `OpenAIProvider` (`openai` SDK for GPT-4o/o3-mini).
  - Provider selection configuration via CLI `--provider` or `agent config`.

---

## 4. Priority Implementation Schedule

| Priority | Feature / Phase | Target Impact | Complexity |
| :---: | :--- | :--- | :--- |
| **P0** | Phase 1: Native Tool Framework | Replaces fragile diff syntax with explicit file tools | Medium |
| **P0** | Phase 2: Native Shell Execution Tool | Enables direct build/test/execution capabilities | Medium |
| **P1** | Phase 4: Real-time Streaming & `prompt_toolkit` | Eliminates response latency perception | Low |
| **P1** | Phase 3: Tree-Sitter Repo Mapping | Dramatically improves multi-file navigation | High |
| **P2** | Phase 5: Multi-Provider Support | Enables switching between Gemini, Claude, and OpenAI | Low |
