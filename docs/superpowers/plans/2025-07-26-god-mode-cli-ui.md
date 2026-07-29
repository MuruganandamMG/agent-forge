# God-Mode CLI UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a high-octane "God-Mode" CLI UI with Cyberpunk themes, ASCII banners, context window usage gauges, linear animated steppers, and structured subagent cards.

**Architecture:** Refactor `agent/runtime/ui.py` into a stateful `UIManager` with helper functions for context window gauge rendering, themes, task headers, pipeline steppers, and subagent cards. Integrate `UIManager` into `scheduler.py`, `chat.py`, `run.py`, and `status.py` while maintaining linear terminal scrollback and passing all tests.

**Tech Stack:** Python 3.10+, Rich (`rich.console`, `rich.panel`, `rich.table`, `rich.syntax`, `rich.text`, `rich.markdown`), pytest.

## Global Constraints

- Retain 100% linear terminal scrollback without clearing screens.
- Use Python standard library and existing `rich` dependency without adding new external libraries.
- Standard unified git diff syntax highlighting for code diffs.
- Context window capacity defaults to 128,000 tokens (for `gemini-2.5-pro`), customizable per model.
- All tests in `pytest` must pass.

---

### Task 1: UI Engine (`agent/runtime/ui.py`) & Context Window Gauge Calculator

**Files:**
- Modify: `agent/runtime/ui.py`
- Create: `tests/test_ui.py`

**Interfaces:**
- Consumes: `rich` console, text, panel, table, syntax, markdown
- Produces:
  - `format_context_gauge(used_tokens: int, limit_tokens: int = 128000, width: int = 20) -> str`
  - `class UIManager`
  - `print_banner(model: str, project_dir: str, file_count: int, context_used: int = 0, context_limit: int = 128000) -> None`
  - `render_task_header(task_id: int, total_tasks: int, goal: str, target_files: list[str] | None = None) -> None`
  - `render_step(step_num: int, total_steps: int, name: str, status: str, detail: str = "") -> None`
  - `render_subagent_card(title: str, content: str, border_style: str = "cyan", is_diff: bool = False) -> None`
  - `render_summary_card(goal: str, completed: list[str], failed: list[str], files_modified: list[str], tokens_used: int = 0, elapsed_sec: float = 0.0) -> None`

- [ ] **Step 1: Write failing tests for UI Engine functions**

Create `tests/test_ui.py`:
```python
import pytest
from agent.runtime.ui import format_context_gauge, UIManager

def test_format_context_gauge_green():
    result = format_context_gauge(used_tokens=10000, limit_tokens=100000, width=10)
    assert "10.0%" in result
    assert "10,000 / 100,000 tokens" in result

def test_format_context_gauge_yellow():
    result = format_context_gauge(used_tokens=60000, limit_tokens=100000, width=10)
    assert "60.0%" in result

def test_format_context_gauge_red():
    result = format_context_gauge(used_tokens=90000, limit_tokens=100000, width=10)
    assert "90.0%" in result

def test_ui_manager_telemetry():
    ui = UIManager()
    ui.add_tokens(5000)
    assert ui.total_tokens == 5000
    ui.add_tokens(3000)
    assert ui.total_tokens == 8000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ui.py -v`
Expected: FAIL with "ImportError" or "cannot import name 'format_context_gauge'"

- [ ] **Step 3: Implement UIManager and helper functions in `agent/runtime/ui.py`**

Update `agent/runtime/ui.py`:
```python
import time
from contextlib import contextmanager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table

console = Console()

def format_context_gauge(used_tokens: int, limit_tokens: int = 128000, width: int = 20) -> str:
    if limit_tokens <= 0:
        limit_tokens = 128000
    pct = min(1.0, max(0.0, used_tokens / limit_tokens))
    filled = int(round(pct * width))
    bar = "█" * filled + "░" * (width - filled)
    pct_str = f"{pct * 100:.1f}%"
    
    if pct < 0.5:
        color = "bold green"
    elif pct < 0.8:
        color = "bold yellow"
    else:
        color = "bold red"
        
    return f"[{color}][{bar}] {pct_str} ({used_tokens:,} / {limit_tokens:,} tokens)[/{color}]"


class UIManager:
    """Centralized UI Manager for God-Mode styling, telemetry, and cards."""
    
    def __init__(self, console_obj: Console = console):
        self.console = console_obj
        self.total_tokens = 0
        self.start_time = time.time()
        
    def add_tokens(self, count: int) -> None:
        if count > 0:
            self.total_tokens += count
            
    def reset_telemetry(self) -> None:
        self.total_tokens = 0
        self.start_time = time.time()
        
    def get_elapsed_sec(self) -> float:
        return time.time() - self.start_time


ui_manager = UIManager()


def print_banner(model: str, project_dir: str, file_count: int, context_used: int = 0, context_limit: int = 128000) -> None:
    """Print the stylized God-Mode startup ASCII banner."""
    ascii_art = (
        "[bold cyan] ⚡ ╔═══════════════════════════════════════════════════════════════════════════╗ ⚡[/bold cyan]\n"
        "[bold magenta] ⚡ ║   ___   ____ _____ _   _ _____   _____ ____  ____   ____ _____           ║ ⚡[/bold magenta]\n"
        "[bold magenta] ⚡ ║  / _ \ / ___| ____| \ | |_   _| |  ___/ __ \|  _ \ / ___| ____|          ║ ⚡[/bold magenta]\n"
        "[bold magenta] ⚡ ║ | |_| | |  _|  _| |  \| | | |   | |_ | |  | | |_) | |  _|  _|            ║ ⚡[/bold magenta]\n"
        "[bold magenta] ⚡ ║ |  _  | |_| | |___| |\  | | |   |  _|| |__| |  _ <| |_| | |___           ║ ⚡[/bold magenta]\n"
        "[bold magenta] ⚡ ║ |_| |_|\____|_____|_| \_| |_|   |_|   \____/|_| \_\\____|_____|          ║ ⚡[/bold magenta]\n"
        "[bold cyan] ⚡ ║                                                                           ║ ⚡[/bold cyan]\n"
        f"[bold yellow] ⚡ ║  Model: [bold white]{model}[/bold white]  │  Project: [bold white]{project_dir}[/bold white]  │  Files: [bold white]{file_count} indexed[/bold white]          ║ ⚡[/bold yellow]\n"
        f" ⚡ ║  Context Window: {format_context_gauge(context_used, context_limit, width=15)}      ║ ⚡\n"
        "[bold cyan] ⚡ ╚═══════════════════════════════════════════════════════════════════════════╝ ⚡[/bold cyan]"
    )
    console.print(ascii_art)


def print_error(msg: str) -> None:
    console.print(f"[bold red]❌ Error:[/bold red] {msg}")


def print_success(msg: str) -> None:
    console.print(f"[bold green]✅ {msg}[/bold green]")


def print_markdown(content: str) -> None:
    console.print(Markdown(content))


def print_diff(diff_content: str) -> None:
    syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=False)
    panel = Panel(syntax, title="[bold cyan]📝 Unified Diff Modifications[/bold cyan]", border_style="cyan", expand=False)
    console.print(panel)


def render_task_header(task_id: int, total_tasks: int, goal: str, target_files: list[str] | None = None) -> None:
    files_str = ", ".join(target_files) if target_files else "Auto-detected"
    text = f"[bold yellow]Goal:[/bold yellow] {goal}\n[bold cyan]Target Files:[/bold cyan] {files_str}"
    panel = Panel(text, title=f"[bold magenta]⚡ [TASK {task_id}/{total_tasks}][/bold magenta]", border_style="magenta", expand=False)
    console.print(panel)


def render_step(step_num: int, total_steps: int, name: str, status: str = "running", detail: str = "") -> None:
    if status == "running":
        badge = "[bold yellow]⏳[/bold yellow]"
    elif status == "done" or status == "passed":
        badge = "[bold green]✓[/bold green]"
    elif status == "failed":
        badge = "[bold red]❌[/bold red]"
    else:
        badge = "[bold blue]•[/bold blue]"
        
    detail_str = f" ... [italic]{detail}[/italic]" if detail else ""
    console.print(f"  {badge} [bold cyan]{step_num}/{total_steps}[/bold cyan] [bold white]{name}[/bold white]{detail_str}")


def render_subagent_card(title: str, content: str, border_style: str = "cyan", is_diff: bool = False) -> None:
    if is_diff:
        body = Syntax(content, "diff", theme="monokai", line_numbers=False)
    else:
        body = Markdown(content) if isinstance(content, str) and content.startswith("#") else Text(str(content))
        
    panel = Panel(body, title=f"[bold]{title}[/bold]", border_style=border_style, expand=False)
    console.print(panel)


def render_summary_card(goal: str, completed: list[str], failed: list[str], files_modified: list[str], tokens_used: int = 0, elapsed_sec: float = 0.0) -> None:
    table = Table(title="[bold magenta]📊 God-Mode Session Summary[/bold magenta]", border_style="magenta")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="bold white")
    
    table.add_row("Goal", goal)
    table.add_row("Completed Tasks", str(len(completed)))
    table.add_row("Failed Tasks", str(len(failed)))
    table.add_row("Files Modified", ", ".join(files_modified) if files_modified else "None")
    table.add_row("Tokens Used", f"{tokens_used:,}" if tokens_used else "N/A")
    table.add_row("Elapsed Time", f"{elapsed_sec:.2f}s" if elapsed_sec > 0 else "N/A")
    
    console.print(table)


@contextmanager
def status_spinner(msg: str):
    with console.status(f"[bold cyan]{msg}...[/bold cyan]", spinner="dots") as status:
        yield status
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ui.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add agent/runtime/ui.py tests/test_ui.py
git commit -m "feat: implement UIManager and context window gauge calculator in ui.py"
```

---

### Task 2: Integrate Pipeline Stepper & Subagent Cards into Scheduler (`agent/runtime/scheduler.py`)

**Files:**
- Modify: `agent/runtime/scheduler.py`
- Modify: `tests/test_scheduler.py` (or existing tests)

**Interfaces:**
- Consumes: `agent/runtime/ui.py` (`render_task_header`, `render_step`, `render_subagent_card`, `render_summary_card`, `format_context_gauge`, `ui_manager`)
- Produces: Enhanced `run_agent` with linear animated stepper stages, diff cards, reviewer critique boxes, and telemetry tracking.

- [ ] **Step 1: Inspect `agent/runtime/scheduler.py` and write test verifying scheduler execution output integration**

Read `tests/` to see existing scheduler test cases:
Run: `pytest tests/ -v`

- [ ] **Step 2: Refactor `run_agent` in `agent/runtime/scheduler.py` to use structured `UIManager` calls**

Modify `agent/runtime/scheduler.py`:
In `run_agent`:
- Reset `ui_manager.reset_telemetry()`
- Replace raw `console.print("[bold cyan]🧠 Planning...[/bold cyan]")` with `render_step(3, 7, "Planner Subagent", "running", "Analyzing goal")`.
- When plan is ready, output `render_step(3, 7, "Planner Subagent", "done", f"Generated {len(task_graph.tasks)} tasks")`.
- Inside the task loop, call `render_task_header(task_id, len(task_graph.tasks), task['description'], task.get("files", []))`.
- For Implementer diff output, call `render_subagent_card("📝 Implementer Unified Diff", diff, border_style="cyan", is_diff=True)`.
- For Validator, call `render_step(6, 7, "Validator", "passed" if vresult.passed else "failed", vresult.stage)`.
- For Reviewer, call `render_subagent_card("🔍 Reviewer Subagent Critique", review, border_style="magenta" if review == "APPROVED" else "yellow")`.
- At task completion, call `render_step(7, 7, "Git Checkpoint", "done", f"Committed {commit_hash[:8]}")`.
- At session summary, call `render_summary_card(task_graph.goal, completed, failed, files_modified, ui_manager.total_tokens, ui_manager.get_elapsed_sec())`.

- [ ] **Step 3: Run existing test suite to ensure zero regressions**

Run: `pytest -v`
Expected: All existing tests PASS.

- [ ] **Step 4: Commit changes**

```bash
git add agent/runtime/scheduler.py
git commit -m "feat: integrate linear pipeline stepper and subagent cards into scheduler"
```

---

### Task 3: Integrate Power-REPL & Context Badges in CLI (`agent/cli/chat.py` & `agent/cli/run.py`)

**Files:**
- Modify: `agent/cli/chat.py`
- Modify: `agent/cli/run.py`

**Interfaces:**
- Consumes: `agent/runtime/ui.py` (`print_banner`, `format_context_gauge`, `console`, `render_subagent_card`)
- Produces: Enhanced `chat_cmd` and `run_cmd` with God-Mode prompt `⚡ god-mode [gemini-2.5-pro] ❯ ` and context window status badges.

- [ ] **Step 1: Update `agent/cli/chat.py`**

Modify `agent/cli/chat.py`:
- Call `print_banner(model, project_dir, file_count, context_used=0, context_limit=128000)` at startup.
- Change input prompt to:
  ```python
  query = console.input(f"[bold magenta]⚡ god-mode[/bold magenta] [bold cyan][{model}][/bold cyan] [bold white]❯[/bold white] ").strip()
  ```
- After receiving/generating response, print the updated context window badge:
  ```python
  context_gauge = format_context_gauge(used_tokens=state.total_tokens if hasattr(state, "total_tokens") else 15000, limit_tokens=128000)
  console.print(f"[dim]Context Window:[/dim] {context_gauge}\n")
  ```

- [ ] **Step 2: Update `agent/cli/run.py`**

Modify `agent/cli/run.py`:
- Call `print_banner(model, project_dir, file_count, context_used=0, context_limit=128000)` at startup.
- Wrap output in God-Mode headers and print summary telemetry upon task completion.

- [ ] **Step 3: Test CLI commands manually via bash**

Run: `pytest -v`
Expected: PASS.

- [ ] **Step 4: Commit changes**

```bash
git add agent/cli/chat.py agent/cli/run.py
git commit -m "feat: add God-Mode prompt and context window status badges to chat and run CLI"
```

---

### Task 4: Glowing Session Status Dashboard (`agent/cli/status.py`)

**Files:**
- Modify: `agent/cli/status.py`

**Interfaces:**
- Consumes: `agent/runtime/session_state.py`, `agent/runtime/ui.py` (`format_context_gauge`, `console`)
- Produces: Rich styled tree & table status panel with telemetry badges.

- [ ] **Step 1: Refactor `agent/cli/status.py` to render God-Mode tree layout**

Modify `agent/cli/status.py`:
- Render session tree with glowing Cyberpunk theme colors (`bold magenta`, `bold cyan`, `bold green`, `bold red`).
- Add Context Window status node to the status tree:
  ```python
  tree.add(f"[bold yellow]⚡ Context Window Usage:[/bold yellow] {format_context_gauge(used_tokens=25000, limit_tokens=128000)}")
  ```

- [ ] **Step 2: Test status command using pytest / bash**

Run: `pytest -v`
Expected: PASS.

- [ ] **Step 3: Commit changes**

```bash
git add agent/cli/status.py
git commit -m "feat: add context window telemetry to agent status command"
```

---

### Task 5: End-to-End Verification & Full Test Suite

**Files:**
- Run full pytest test suite across all runtime and CLI modules.

- [ ] **Step 1: Run full pytest test suite**

Run: `pytest -v`
Expected: 100% tests PASS.

- [ ] **Step 2: Final commit & verify git branch clean**

Run: `git status`
Expected: Clean working tree.
