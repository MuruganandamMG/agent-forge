# CLI Entrypoint & Main.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure `agent` as a global CLI command via `pyproject.toml` and update `agent/runtime/main.py` with version info, API key verification, and command help.

**Architecture:** Add `[project.scripts]` to `agent/pyproject.toml` pointing to `runtime.main:main`. Refactor `agent/runtime/main.py` with `@click.version_option()`, pre-execution API key check, and click command routing.

**Tech Stack:** Python 3.11+, Click, Setuptools / pip.

## Global Constraints

- Must allow running `agent chat`, `agent run`, `agent status`, and `agent config`.
- Must allow running via `PYTHONPATH=agent python -m runtime.main` as fallback.

---

### Task 1: Update `agent/pyproject.toml` & `agent/runtime/main.py`

**Files:**
- Modify: `agent/pyproject.toml`
- Modify: `agent/runtime/main.py`
- Modify: `tests/test_ui.py` (or new `tests/test_main.py`)

**Interfaces:**
- Consumes: `click`
- Produces: Global `agent` CLI script entry point

- [ ] **Step 1: Write failing test for main CLI options**

Create `tests/test_main.py`:
```python
from click.testing import CliRunner
from runtime.main import main

def test_main_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Local Coding Agent" in result.output

def test_main_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
```

- [ ] **Step 2: Run test to verify failure**

Run: `PYTHONPATH=agent pytest tests/test_main.py -v`
Expected: FAIL on version check (version option not yet configured)

- [ ] **Step 3: Update `agent/pyproject.toml` and `agent/runtime/main.py`**

Add `[project.scripts]` to `agent/pyproject.toml`:
```toml
[project.scripts]
agent = "runtime.main:main"
```

Update `agent/runtime/main.py`:
```python
"""CLI entry point for the local coding agent."""

import os
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
VERSION = "0.1.0"


@click.group(invoke_without_command=True)
@click.version_option(version=VERSION, prog_name="agent-forge")
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
    """⚡ Local Coding Agent (agent-forge) — autonomous coding assistant."""
    ctx.ensure_object(dict)
    project_dir = str(Path(project).resolve())
    ctx.obj['project_dir'] = project_dir
    ctx.obj['model'] = model

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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

- [ ] **Step 4: Run test to verify pass**

Run: `PYTHONPATH=agent pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add agent/pyproject.toml agent/runtime/main.py tests/test_main.py
git commit -m "feat: configure agent CLI script entry point and version flag"
```
