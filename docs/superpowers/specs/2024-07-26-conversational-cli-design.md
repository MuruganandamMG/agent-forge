# Conversational CLI Design (Hybrid Orchestrator)

## Overview
Currently, the CLI uses an input gate (`gate.py`) to intercept non-coding queries (`trivial`, `vague`, `chat`) and responds with hard-coded static strings. The goal is to modernize this by routing these queries to a lightweight, conversational LLM endpoint that maintains chat history, making the CLI feel as dynamic and conversational as Claude Code or Pi CLI. 

Actionable coding tasks will continue to be routed to the heavy `run_agent()` pipeline.

## Components to Update

### 1. Conversation History (Memory)
- We need a mechanism to store recent chat interactions so that conversational replies have context (e.g., if a user says "hello", and then "what is this project?").
- We will add a simple `chat_history` list to the existing session state in `agent/runtime/session_state.py`.
- We will define a `max_history` limit (e.g., last 10 messages) to prevent token bloat.

### 2. Conversational Responder (`agent/runtime/chat_responder.py`)
- Introduce a new module with a function `generate_chat_response(query: str, history: list, project_context: str) -> str`.
- This function will construct a system prompt explaining that the AI is the Forge Coding Agent, currently engaged in a conversational turn.
- It will call `models.chat()` directly, providing a fast, dynamic response without triggering the full task execution sandbox.

### 3. CLI Routing (`agent/cli/chat.py` & `agent/cli/run.py`)
- Instead of printing `🙂 Tell me what you'd like me to build...`, the CLI will call `generate_chat_response()`.
- The CLI will print the LLM's dynamic response to the console.
- Both the user query and the LLM response will be appended to the `chat_history` in `session_state`.
- Task queries routed to `run_agent` will also append a summary of their action to `chat_history` so the chat LLM remains aware of recent coding actions.

## Architecture

```
User Input -> classify_input (gate.py)
  |
  |-- if 'task' -> run_agent (Heavy tool loop, modifies files) -> Append action summary to chat_history
  |
  |-- if 'trivial', 'vague', 'chat' -> generate_chat_response (Lightweight conversational LLM) -> Append to chat_history
```

## Constraints
- Do not remove `gate.py`. It is crucial for routing between the lightweight and heavyweight pipelines.
- Ensure `models.chat()` is utilized correctly for the lightweight responses.
- Ensure the updated `session_state.json` schema remains backward compatible or gracefully handles old session files.
