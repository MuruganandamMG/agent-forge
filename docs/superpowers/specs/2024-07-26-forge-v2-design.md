# Forge 2.0: Advanced CLI Coding Agent Enhancements

## Overview
The user has authorized a comprehensive overhaul of the Forge CLI coding agent to transform it into a long-term, highly capable agentic platform. The goal is to move beyond a single-model, single-file context approach into a modular, multi-model, multi-agent system equipped with RAG (Retrieval-Augmented Generation) and rich terminal feedback.

## Pillar 1: Multi-Model & Provider Abstraction
Currently, the agent is hardcoded to `gemini-2.5-pro` via the `google.genai` SDK in `models.py`. 
- **Design:** Introduce a `Provider` interface. 
- **Implementation:** Create `agent/runtime/providers/` with `gemini.py`, `openai.py`, `anthropic.py`, and `ollama.py`. 
- **Router:** `models.py` becomes a factory that reads the CLI `--model` or config file to instantiate the correct provider, normalizing message formats and function-calling schemas.

## Pillar 2: Subagent Architecture (The "Forge Team")
The agent currently uses a single execution loop (`run_agent`). 
- **Design:** Implement a robust Subagent system natively.
- **Agents:**
  - `Planner`: Analyzes requests and breaks them into a graph of sub-tasks.
  - `Researcher`: Uses ChromaDB to semantically search the codebase and documentation to answer context queries.
  - `Coder`: Executes exact file modifications.
  - `Reviewer`: Critiques diffs before they are finalized.
- **Implementation:** Expand `task_graph.py` and `scheduler.py` to route tasks to these specific personas based on tags.

## Pillar 3: Semantic Codebase RAG (Long-Term Memory)
`chromadb` is in `requirements.txt` but the agent currently reads raw files or uses a simple file tree. 
- **Design:** Add an `agent/runtime/vector_store.py` module.
- **Implementation:** On startup (or via a new `agent index` command), chunk and embed all `.py`, `.js`, `.md`, etc. files into a local ChromaDB instance stored in `.agent_memory/`. 
- **Usage:** When the codebase exceeds the context window, the `Researcher` agent queries the vector database to inject only the relevant code snippets into the `Coder`'s prompt.

## Pillar 4: Rich Terminal UI (UX Polish)
- **Design:** Replace standard `print()` statements with `rich` library components (already in requirements).
- **Implementation:** Add Live layout panels for streaming LLM tokens, Syntax highlighted code diffs, and Tree views for the file index. 

## Decomposition & Execution Strategy
Due to the massive scope, this will be executed in sequential phases:
1. **Phase 1:** Multi-Model Support (Provider Abstraction)
2. **Phase 2:** Rich UI & Streaming Integration
3. **Phase 3:** Subagent Delegation Framework
4. **Phase 4:** ChromaDB Vector RAG implementation

*Self-Review Note:* Ambiguity resolved. The architecture relies on standard REST/SDK wrappers for models. Scope is large but decomposed. No placeholders.

*User Override:* The user explicitly bypassed the review gate. Proceeding directly to implementation plan generation and execution.
