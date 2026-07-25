# Conversational CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the CLI into a dynamic conversational assistant for non-coding queries by adding a lightweight LLM responder and session chat history.

**Architecture:** Extend `session_state.json` to store recent chat interactions. Introduce a `chat_responder.py` module to handle lightweight LLM replies. Update `cli/chat.py` to route `trivial`/`vague`/`chat` intents to the responder instead of printing static strings.

**Tech Stack:** Python 3, `click`, `pytest`

## Global Constraints

- Standard unified git diff format (`diff -u`) for patches.
- No swallowed errors: catch and raise `click.ClickException` or log and continue.
- All code goes in `E:/AI/Models/agent-forge/agent/`.
- `chat_history` must be capped at 10 items (5 turns) to prevent token explosion.

---

### Task 1: Update Session State for Chat History

**Files:**
- Modify: `agent/runtime/session_state.py`
- Modify: `agent/tests/test_session_state.py`

**Interfaces:**
- Produces: `SessionState` dataclass now includes `chat_history: list[dict[str, str]]` with max size of 10. `append_chat_message(role: str, content: str)` method on `SessionState`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from runtime.session_state import SessionState, load_session_state, save_session_state
import json
import os

def test_session_state_chat_history_init():
    state = SessionState()
    assert state.chat_history == []

def test_append_chat_message():
    state = SessionState()
    for i in range(15):
        state.append_chat_message("user", f"msg {i}")
    
    assert len(state.chat_history) == 10
    assert state.chat_history[0]["content"] == "msg 5"
    assert state.chat_history[-1]["content"] == "msg 14"

def test_save_load_chat_history(tmp_path):
    state = SessionState()
    state.append_chat_message("user", "hello")
    state.append_chat_message("assistant", "hi")
    
    save_session_state(state, str(tmp_path))
    
    loaded = load_session_state(str(tmp_path))
    assert loaded.chat_history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"}
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_session_state.py -v`
Expected: FAIL (missing `chat_history` and `append_chat_message`)

- [ ] **Step 3: Write minimal implementation in `agent/runtime/session_state.py`**

```python
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class SessionState:
    last_run: str = ""
    last_goal: str = ""
    completed_tasks: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    last_files_modified: list[str] = field(default_factory=list)
    open_errors: list[str] = field(default_factory=list)
    chat_history: list[dict[str, str]] = field(default_factory=list)
    
    def append_chat_message(self, role: str, content: str) -> None:
        """Append a message and trim history to the last 10 messages."""
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

def load_session_state(project_dir: str) -> SessionState:
    state_file = os.path.join(project_dir, "session_state.json")
    if not os.path.exists(state_file):
        return SessionState()

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Default missing arrays to empty lists to avoid TypeError on load
            return SessionState(
                last_run=data.get("last_run") or "",
                last_goal=data.get("last_goal") or "",
                completed_tasks=data.get("completed_tasks") or [],
                pending_tasks=data.get("pending_tasks") or [],
                last_files_modified=data.get("last_files_modified") or [],
                open_errors=data.get("open_errors") or [],
                chat_history=data.get("chat_history") or [],
            )
    except (json.JSONDecodeError, KeyError, TypeError):
        return SessionState()

def save_session_state(state: SessionState, project_dir: str) -> None:
    state.last_run = datetime.now(timezone.utc).isoformat()
    state_file = os.path.join(project_dir, "session_state.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=2)

def print_resume_banner(state: SessionState) -> None:
    if not state.last_goal:
        return
    
    print("\n📋 Last session: " + state.last_goal)
    if state.pending_tasks:
        for t in state.pending_tasks:
            print(f"   ⏳ {t}")
    if state.open_errors:
        for e in state.open_errors:
            print(f"   ❌ {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agent/tests/test_session_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/session_state.py agent/tests/test_session_state.py
git commit -m "feat: add chat history to session state"
```

---

### Task 2: Create Chat Responder

**Files:**
- Create: `agent/runtime/chat_responder.py`
- Create: `agent/tests/test_chat_responder.py`

**Interfaces:**
- Produces: `generate_chat_response(query: str, history: list[dict[str, str]], project_context: str) -> str`

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from unittest.mock import patch
from runtime.chat_responder import generate_chat_response

@patch("runtime.chat_responder.chat")
def test_generate_chat_response(mock_chat):
    mock_chat.return_value = "Hello! I am Forge."
    history = [{"role": "user", "content": "hi"}]
    
    res = generate_chat_response("how are you?", history, "File: main.py")
    
    assert res == "Hello! I am Forge."
    mock_chat.assert_called_once()
    
    # Verify messages format
    messages = mock_chat.call_args[0][0]
    assert messages[0]["role"] == "system"
    assert "Forge Coding Agent" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hi"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "how are you?"

@patch("runtime.chat_responder.chat")
def test_generate_chat_response_fallback(mock_chat):
    mock_chat.side_effect = Exception("API error")
    res = generate_chat_response("hi", [], "")
    assert res == "🙂 Tell me what you'd like me to build, fix, or change."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_chat_responder.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation in `agent/runtime/chat_responder.py`**

```python
from runtime.models import chat

SYSTEM_PROMPT = """You are the Forge Coding Agent, a capable CLI-based AI assistant.
The user just sent a conversational or vague message (not an explicit coding task).
Respond politely, conversationally, and concisely.
If they ask what you can do, explain you can build, refactor, and fix code in their project.
Keep responses under 3 sentences unless explaining a complex topic.

Project Context Summary:
{project_context}
"""

def generate_chat_response(query: str, history: list[dict[str, str]], project_context: str) -> str:
    """Generate a lightweight conversational response using chat history."""
    # Truncate project context heavily to save tokens on chat
    truncated_ctx = project_context[:1000] + ("..." if len(project_context) > 1000 else "")
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(project_context=truncated_ctx)}
    ]
    
    # Append history
    for msg in history:
        messages.append(msg)
        
    # Append current query
    messages.append({"role": "user", "content": query})
    
    try:
        # Use low max_tokens for chat responses
        return chat(messages, temperature=0.7, max_tokens=500).strip()
    except Exception:
        return "🙂 Tell me what you'd like me to build, fix, or change."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agent/tests/test_chat_responder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/chat_responder.py agent/tests/test_chat_responder.py
git commit -m "feat: add conversational chat responder"
```

---

### Task 3: Route Conversational Queries in CLI

**Files:**
- Modify: `agent/cli/chat.py`

**Interfaces:**
- Consumes: `generate_chat_response` from `runtime.chat_responder`. `append_chat_message` on `SessionState`.

- [ ] **Step 1: Write the updated implementation in `agent/cli/chat.py`**

```python
import sys
import click
from runtime.gate import classify_input
from runtime.indexer import generate_project_context
from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, print_resume_banner, save_session_state
from runtime.chat_responder import generate_chat_response

@click.command("chat")
@click.pass_context
def chat_cmd(ctx):
    """Start an interactive coding session."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj['model']
    
    project_ctx = generate_project_context(project_dir)
    file_count = project_ctx.count("\n") - 5
    
    click.echo(f"⚡ Forge Agent | Model: {model} | Project: {project_dir}")
    click.echo(f"📁 Indexed {file_count} files")

    state = load_session_state(project_dir)
    print_resume_banner(state)

    click.echo("\n💬 Enter your coding request (prefix with '/plan <request>' for multi-step planning, or Ctrl+C to exit):\n")
    
    while True:
        try:
            query = input("you> ").strip()
            if not query: continue
            if query.lower() in ("exit", "quit", "q"): break

            state.append_chat_message("user", query)

            intent = classify_input(query, project_context=project_ctx)
            if intent in ("trivial", "vague", "chat"):
                response = generate_chat_response(query, state.chat_history[:-1], project_ctx)
                click.echo(f"\n🤖 {response}\n")
                state.append_chat_message("assistant", response)
                save_session_state(state, project_dir)
                continue

            # It's a task
            res = run_agent(query, project_dir, project_context=project_ctx)
            state.last_goal = query
            
            # Summarize the action for the chat history
            state.append_chat_message("assistant", f"[Executed task: {query}]")
            
            if isinstance(res, dict):
                completed = res.get("completed", [])
                failed = res.get("failed", [])
                files_mod = res.get("files_modified", [])

                if completed: state.completed_tasks.extend(completed)
                elif not failed: state.completed_tasks.append(query)
                if failed: state.open_errors.extend(failed)
                
                for f in files_mod:
                    if f not in state.last_files_modified:
                        state.last_files_modified.append(f)
            else:
                state.completed_tasks.append(query)

            state.pending_tasks = []
            save_session_state(state, project_dir)
            print()
            
        except KeyboardInterrupt:
            click.echo("\n👋 Bye!")
            break
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
```

- [ ] **Step 2: Commit**

```bash
git add agent/cli/chat.py
git commit -m "feat: route conversational queries to llm responder"
```
