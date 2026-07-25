# CLI Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the single-file `main.py` entry point into a modular, multi-command CLI using the `click` framework.

**Architecture:** A `@click.group` root command in `agent/runtime/main.py` that delegates to specialized subcommands in a new `agent/cli/` package (`chat`, `run`, `config`, `status`).

**Tech Stack:** Python 3, `click`, `pytest`

## Global Constraints

- Must use `click` framework for all CLI routing and arguments.
- Standard unified git diff format (`diff -u`) for patches.
- No swallowed errors: catch and raise `click.ClickException`.
- All paths resolved from project root.
- The root CLI command (`agent`) accepts `--project` and `--model` globally.
- No UI logic (like click.echo) deeply embedded in core runtime/ modules except where already present; keep CLI formatting in the `cli/` module.
- All code goes in `E:/AI/Models/agent-forge/agent/`

---

### Task 1: Create CLI Package and Base Group

**Files:**
- Create: `agent/cli/__init__.py`
- Modify: `agent/runtime/main.py`
- Create: `agent/tests/test_cli_main.py`

**Interfaces:**
- Produces: `cli_group` click command group object. `Click Context (ctx.obj)` dictionary containing `project_dir` and `model`.

- [ ] **Step 1: Write the failing test for the root group**

```python
import click
from click.testing import CliRunner
from runtime.main import main

def test_root_command_requires_subcommand():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code != 0
    assert "Missing command" in result.output

def test_root_command_accepts_global_options():
    runner = CliRunner()
    result = runner.invoke(main, ['--project', '.', '--model', 'test-model', 'chat'])
    # Will fail until chat is implemented, but should parse args
    assert "No such command" in result.output or result.exit_code != 2 # Not a usage error for globals
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_cli_main.py -v`
Expected: FAIL (because `main.py` is currently a `@click.command`, not `@click.group`)

- [ ] **Step 3: Write minimal implementation in `agent/runtime/main.py`**

Refactor `main.py` to strip out the REPL loop and make it a group.

```python
"""CLI entry point for the local coding agent."""
import sys
from pathlib import Path
import click

if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try: sys.stderr.reconfigure(encoding="utf-8")
        except Exception: pass

DEFAULT_MODEL = "gemini-2.5-pro"

@click.group(invoke_without_command=False)
@click.option("--project", "-p", type=click.Path(exists=True, file_okay=False), default=".", help="Path to the project directory.")
@click.option("--model", "-m", type=str, default=DEFAULT_MODEL, help="Name of the Gemini model to use.")
@click.pass_context
def main(ctx, project: str, model: str):
    """Local Coding Agent — autonomous coding assistant."""
    ctx.ensure_object(dict)
    project_dir = str(Path(project).resolve())
    ctx.obj['project_dir'] = project_dir
    ctx.obj['model'] = model

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create empty `agent/cli/__init__.py`**
```bash
mkdir -p agent/cli
touch agent/cli/__init__.py
```

- [ ] **Step 5: Run test to verify root structure**

Run: `pytest agent/tests/test_cli_main.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/runtime/main.py agent/cli/__init__.py agent/tests/test_cli_main.py
git commit -m "feat: convert main entrypoint to click group"
```

---

### Task 2: Implement Chat Subcommand (REPL)

**Files:**
- Create: `agent/cli/chat.py`
- Modify: `agent/runtime/main.py`
- Create: `agent/tests/test_cli_chat.py`

**Interfaces:**
- Consumes: `ctx.obj['project_dir']`, `ctx.obj['model']` from `main.py`. `generate_project_context`, `load_agents_md`, `generate_filetree`, `classify_input`, `run_agent`, `load_session_state`, `save_session_state` from `agent.runtime`.

- [ ] **Step 1: Write the failing test**

```python
import click
from click.testing import CliRunner
from cli.chat import chat_cmd

def test_chat_command_help():
    runner = CliRunner()
    result = runner.invoke(chat_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Start an interactive coding session" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_cli_chat.py -v`
Expected: FAIL (chat_cmd does not exist)

- [ ] **Step 3: Write implementation in `agent/cli/chat.py`**

Move the REPL loop logic from the old `main.py` into this command.

```python
import click
from runtime.context import load_agents_md
from runtime.filetree import generate_filetree
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
    
    click.echo(f"🏠 Project: {project_dir}")
    click.echo(f"🤖 Model: {model}")
    print("🔍 Indexing project...")
    
    project_ctx = generate_project_context(project_dir)
    agents_md = load_agents_md(project_dir)
    file_tree = generate_filetree(project_dir)
    
    if agents_md:
        click.echo("📜 Loaded AGENTS.md project rules")
    file_count = project_ctx.count("\n") - 5
    print(f"📁 Indexed {file_count} files")

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

- [ ] **Step 4: Register subcommand in `agent/runtime/main.py`**

Add to `agent/runtime/main.py`:
```python
from cli.chat import chat_cmd
# (after main definition)
main.add_command(chat_cmd)
```

- [ ] **Step 5: Run tests**

Run: `pytest agent/tests/test_cli_chat.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/cli/chat.py agent/runtime/main.py agent/tests/test_cli_chat.py
git commit -m "feat: add chat repl subcommand"
```

---

### Task 3: Implement Run Subcommand (Single-Shot)

**Files:**
- Create: `agent/cli/run.py`
- Modify: `agent/runtime/main.py`
- Create: `agent/tests/test_cli_run.py`

**Interfaces:**
- Consumes: `ctx.obj['project_dir']`, `ctx.obj['model']`. Core execution functions same as chat.

- [ ] **Step 1: Write the failing test**

```python
import click
from click.testing import CliRunner
from cli.run import run_cmd
from unittest.mock import patch

def test_run_command_help():
    runner = CliRunner()
    result = runner.invoke(run_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Execute a single task" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_cli_run.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation in `agent/cli/run.py`**

```python
import click
import os
from runtime.context import load_agents_md
from runtime.filetree import generate_filetree
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
    
    # Handle if input is a file path
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

    click.echo(f"🏠 Project: {project_dir}")
    print("🔍 Indexing project...")
    
    project_ctx = generate_project_context(project_dir)
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
    except Exception as e:
        raise click.ClickException(str(e))
```

- [ ] **Step 4: Register subcommand in `agent/runtime/main.py`**

Add to `agent/runtime/main.py`:
```python
from cli.run import run_cmd
# (after main definition)
main.add_command(run_cmd)
```

- [ ] **Step 5: Run tests**

Run: `pytest agent/tests/test_cli_run.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/cli/run.py agent/runtime/main.py agent/tests/test_cli_run.py
git commit -m "feat: add run single-shot subcommand"
```

---

### Task 4: Implement Status Subcommand

**Files:**
- Create: `agent/cli/status.py`
- Modify: `agent/runtime/main.py`
- Create: `agent/tests/test_cli_status.py`

**Interfaces:**
- Consumes: `ctx.obj['project_dir']`, `load_session_state` from `runtime.session_state`.

- [ ] **Step 1: Write the failing test**

```python
import click
from click.testing import CliRunner
from cli.status import status_cmd

def test_status_command_help():
    runner = CliRunner()
    result = runner.invoke(status_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Show current session status" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_cli_status.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation in `agent/cli/status.py`**

```python
import click
from runtime.session_state import load_session_state

@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show current session status and history."""
    project_dir = ctx.obj['project_dir']
    state = load_session_state(project_dir)
    
    click.echo(f"📊 Session Status for {project_dir}")
    click.echo("-" * 40)
    
    if state.last_goal:
        click.echo(f"🎯 Last Goal: {state.last_goal}")
    else:
        click.echo("🎯 Last Goal: None")
        
    click.echo("\n✅ Completed Tasks:")
    if state.completed_tasks:
        for task in state.completed_tasks[-5:]: # show last 5
            click.echo(f"  - {task}")
    else:
        click.echo("  (None)")
        
    click.echo("\n⏳ Pending Tasks:")
    if state.pending_tasks:
        for task in state.pending_tasks:
            click.echo(f"  - {task}")
    else:
        click.echo("  (None)")
        
    click.echo("\n❌ Open Errors:")
    if state.open_errors:
        for err in state.open_errors:
            click.echo(f"  - {err}", err=True)
    else:
        click.echo("  (None)")
        
    click.echo("\n📝 Recently Modified Files:")
    if state.last_files_modified:
        for f in state.last_files_modified[-5:]:
            click.echo(f"  - {f}")
    else:
        click.echo("  (None)")
```

- [ ] **Step 4: Register subcommand in `agent/runtime/main.py`**

Add to `agent/runtime/main.py`:
```python
from cli.status import status_cmd
# (after main definition)
main.add_command(status_cmd)
```

- [ ] **Step 5: Run tests**

Run: `pytest agent/tests/test_cli_status.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/cli/status.py agent/runtime/main.py agent/tests/test_cli_status.py
git commit -m "feat: add status session reporting subcommand"
```

---

### Task 5: Implement Config Subcommand

**Files:**
- Create: `agent/cli/config.py`
- Modify: `agent/runtime/main.py`
- Create: `agent/tests/test_cli_config.py`

**Interfaces:**
- Consumes: local `.agent_config.json` inside project directory.

- [ ] **Step 1: Write the failing test**

```python
import click
from click.testing import CliRunner
from cli.config import config_cmd

def test_config_command_help():
    runner = CliRunner()
    result = runner.invoke(config_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Manage workspace configuration" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_cli_config.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation in `agent/cli/config.py`**

```python
import click
import json
import os

CONFIG_FILE = ".agent_config.json"

def load_config(project_dir: str) -> dict:
    config_path = os.path.join(project_dir, CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(project_dir: str, config: dict):
    config_path = os.path.join(project_dir, CONFIG_FILE)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

@click.group("config")
def config_cmd():
    """Manage workspace configuration."""
    pass

@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    project_dir = ctx.obj['project_dir']
    config = load_config(project_dir)
    config[key] = value
    save_config(project_dir, config)
    click.echo(f"✅ Set {key} = {value}")

@config_cmd.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx, key):
    """Get a configuration value."""
    project_dir = ctx.obj['project_dir']
    config = load_config(project_dir)
    val = config.get(key)
    if val is not None:
        click.echo(f"{key} = {val}")
    else:
        click.echo(f"❌ Key '{key}' not found.")

@config_cmd.command("list")
@click.pass_context
def config_list(ctx):
    """List all configuration values."""
    project_dir = ctx.obj['project_dir']
    config = load_config(project_dir)
    if not config:
        click.echo("No configuration found.")
        return
    click.echo("⚙️ Current Configuration:")
    for k, v in config.items():
        click.echo(f"  {k}: {v}")
```

- [ ] **Step 4: Register subcommand in `agent/runtime/main.py`**

Add to `agent/runtime/main.py`:
```python
from cli.config import config_cmd
# (after main definition)
main.add_command(config_cmd)
```

- [ ] **Step 5: Run tests**

Run: `pytest agent/tests/test_cli_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/cli/config.py agent/runtime/main.py agent/tests/test_cli_config.py
git commit -m "feat: add config management subcommand"
```
