# CLI Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the CLI architecture by completely removing the legacy `llama-server` process management logic and polishing the startup banners.

**Architecture:** Remove legacy flags from `main.py` (`--port`, `--ctx-size`, `--server-bin`), remove `health_check` and `ensure_server` from `models.py`, update `chat.py` and `run.py` to print a single unified startup banner, and update all affected tests.

**Tech Stack:** Python 3, `click`, `pytest`

## Global Constraints

- Must use standard unified git diff format (`diff -u`) for patches.
- No swallowed errors: catch and raise `click.ClickException`.
- All paths resolved from project root (`E:/AI/Models/agent-forge/agent/`).
- The root CLI command (`agent`) accepts only `--project` and `--model` globally.
- Clean and unified CLI output (e.g., `⚡ Forge Agent | Model: gemini-2.5-pro | Project: <path>`).

---

### Task 1: Clean Up `main.py`

**Files:**
- Modify: `agent/runtime/main.py`

**Interfaces:**
- Produces: `ctx.obj` containing only `project_dir` and `model`.

- [ ] **Step 1: Write the updated implementation in `agent/runtime/main.py`**

Remove the `port`, `ctx_size`, and `server_bin` click options and context variables.

```python
"""CLI entry point for the local coding agent."""

import sys
from pathlib import Path

if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

import click

DEFAULT_MODEL = "gemini-2.5-pro"

@click.group(invoke_without_command=False)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Path to the project directory to work on.",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default=DEFAULT_MODEL,
    help="Name of the Gemini model to use.",
)
@click.pass_context
def main(ctx: click.Context, project: str, model: str) -> None:
    """Local Coding Agent — autonomous coding assistant."""
    ctx.ensure_object(dict)
    project_dir = str(Path(project).resolve())
    ctx.obj['project_dir'] = project_dir
    ctx.obj['model'] = model

from cli.chat import chat_cmd
from cli.run import run_cmd
from cli.status import status_cmd
from cli.config import config_cmd
main.add_command(chat_cmd)
main.add_command(run_cmd)
main.add_command(status_cmd)
main.add_command(config_cmd)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add agent/runtime/main.py
git commit -m "refactor: remove legacy server flags from main group"
```

---

### Task 2: Polish `chat.py` and `run.py`

**Files:**
- Modify: `agent/cli/chat.py`
- Modify: `agent/cli/run.py`

**Interfaces:**
- Consumes: `ctx.obj['project_dir']` and `ctx.obj['model']` only.

- [ ] **Step 1: Write the updated implementation in `agent/cli/chat.py`**

Remove the legacy ctx options and the ugly multi-line banner. Create one unified banner.

```python
import sys
import click
from runtime.gate import classify_input
from runtime.indexer import generate_project_context
from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, print_resume_banner, save_session_state

@click.command("chat")
@click.pass_context
def chat_cmd(ctx):
    """Start an interactive coding session."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj['model']
    
    project_ctx = generate_project_context(project_dir)
    file_count = project_ctx.count("\n") - 5
    
    # Unified banner
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

            intent = classify_input(query, project_context=project_ctx)
            if intent == "trivial":
                click.echo("🙂 Tell me what you'd like me to build, fix, or change.\n")
                continue
            if intent == "vague":
                click.echo("❓ Can you give me more detail — which file, what behavior?\n")
                continue
            if intent == "chat":
                click.echo("💬 Let's focus on your coding project! What would you like to build or fix?\n")
                continue

            res = run_agent(query, project_dir, project_context=project_ctx)
            state.last_goal = query
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

- [ ] **Step 2: Write the updated implementation in `agent/cli/run.py`**

Remove the legacy ctx options and the ugly multi-line banner. 

```python
import click
import os
import sys
from runtime.gate import classify_input
from runtime.indexer import generate_project_context
from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, save_session_state

@click.command("run")
@click.argument("task_input", nargs=-1, required=True)
@click.pass_context
def run_cmd(ctx, task_input):
    """Execute a single task from text or a file and exit."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj['model']
    
    input_str = " ".join(task_input).strip()
    file_path = os.path.join(project_dir, input_str)
    
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            query = f.read().strip()
            click.echo(f"📄 Loaded task from {input_str}")
    else:
        query = input_str
        
    if not query:
        raise click.ClickException("Task input cannot be empty.")

    project_ctx = generate_project_context(project_dir)
    file_count = project_ctx.count("\n") - 5
    
    # Unified banner
    click.echo(f"⚡ Forge Agent | Model: {model} | Project: {project_dir}")
    click.echo(f"📁 Indexed {file_count} files")
    
    state = load_session_state(project_dir)
    
    try:
        intent = classify_input(query, project_context=project_ctx)
        if intent in ("trivial", "vague", "chat"):
            raise click.ClickException(f"Input classified as '{intent}'. Please provide a clear coding task.")
            
        res = run_agent(query, project_dir, project_context=project_ctx)
        state.last_goal = query
        
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
        click.echo("✅ Task complete.")
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e))
```

- [ ] **Step 3: Commit**

```bash
git add agent/cli/chat.py agent/cli/run.py
git commit -m "refactor: polish cli banners and remove legacy server logic"
```

---

### Task 3: Remove Dead Code in `models.py`

**Files:**
- Modify: `agent/runtime/models.py`
- Modify: `agent/tests/test_models.py`

**Interfaces:**
- Produces: Cleaner `models.py` containing only `chat` and `count_tokens`.

- [ ] **Step 1: Write the minimal implementation in `agent/runtime/models.py`**

The `models.py` file is already clean but may contain leftover imports. Let's make sure it's pristine.

```python
import sys
from typing import Any

from google import genai
from google.genai import types

if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def chat(
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 4096,
    stop: list[str] | None = None,
) -> str:
    """Send a chat completion request to Gemini API and return the assistant response text."""
    client = genai.Client()
    system_instruction = None
    
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        else:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            contents.append(
                types.Content(
                    role=role, 
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        stop_sequences=stop,
    )
    
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=contents,
        config=config
    )
    
    if response.text is None:
        return ""
    return response.text


def count_tokens(text: str) -> int:
    """Estimate token count using a simple chars/4 heuristic."""
    if not text:
        return 0
    return len(text) // 4
```

- [ ] **Step 2: Update `agent/tests/test_models.py`**

Remove the tests for `health_check` and `ensure_server`.

```python
import pytest
from unittest.mock import patch, MagicMock
from runtime.models import chat, count_tokens

class TestChat:
    @patch("runtime.models.genai.Client")
    def test_chat_returns_assistant_content(self, mock_client_class):
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "I am an AI."
        mock_client.models.generate_content.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Who are you?"},
        ]
        
        result = chat(messages)
        
        assert result == "I am an AI."
        mock_client.models.generate_content.assert_called_once()

    @patch("runtime.models.genai.Client")
    def test_chat_sends_correct_parameters(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_client.models.generate_content.return_value = mock_response

        messages = [{"role": "user", "content": "hi"}]
        chat(messages, temperature=0.7, max_tokens=100)

        _, kwargs = mock_client.models.generate_content.call_args
        assert kwargs["model"] == "gemini-2.5-pro"
        assert kwargs["config"].temperature == 0.7
        assert kwargs["config"].max_output_tokens == 100

class TestCountTokens:
    def test_count_tokens_empty_string(self):
        assert count_tokens("") == 0

    def test_count_tokens_400_chars(self):
        # 400 chars / 4 = 100 tokens
        text = "a" * 400
        assert count_tokens(text) == 100
```

- [ ] **Step 3: Run tests to verify everything is green**

Run: `pytest agent/tests/ -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add agent/runtime/models.py agent/tests/test_models.py
git commit -m "refactor: remove legacy server tests and code from models"
```
