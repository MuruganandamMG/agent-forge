# Auto-Healing, Context Repo-Map, and TUI Completer Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add slash command auto-completion, integrate symbol repo-mapping into context assembly, and enable auto-healing test retry loops in scheduler.

**Architecture:** Attach `WordCompleter` to `prompt_toolkit` session, include `generate_repo_map` output in `build_context`, and pass `last_error` into `run_tool_agent` on retry attempts.

**Tech Stack:** Python 3.13, prompt_toolkit, pytest.

---

### Task 1: Slash Command Auto-Completer (`agent/cli/tui.py`)

**Files**:
- Modify: `agent/cli/tui.py`
- Test: `agent/tests/test_tui_completer.py`

- [ ] **Step 1: Write failing test**

Create `agent/tests/test_tui_completer.py`:
```python
from cli.tui import get_slash_completer

def test_get_slash_completer():
    completer = get_slash_completer()
    words = completer.words
    assert "/plan" in words
    assert "/status" in words
    assert "/help" in words
```

- [ ] **Step 2: Run test to verify it fails**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_tui_completer.py`
Expected: FAIL.

- [ ] **Step 3: Implement `get_slash_completer` in `agent/cli/tui.py`**

In `agent/cli/tui.py`:
Import `WordCompleter` from `prompt_toolkit.completion` and implement `get_slash_completer()`. Attach to `PromptSession`.

- [ ] **Step 4: Run test to verify it passes**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_tui_completer.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/cli/tui.py agent/tests/test_tui_completer.py
git commit -m "feat(cli): add prompt_toolkit slash command completer"
```

---

### Task 2: Repo-Map Context Assembly Integration (`agent/runtime/context.py`)

**Files**:
- Modify: `agent/runtime/context.py`
- Test: `agent/tests/test_context_repo_map.py`

- [ ] **Step 1: Write failing test**

Create `agent/tests/test_context_repo_map.py`:
```python
from unittest.mock import MagicMock
from runtime.context import build_context

def test_build_context_includes_repo_map(tmp_path):
    f = tmp_path / "foo.py"
    f.write_text("def my_func(): pass", encoding="utf-8")

    mem = MagicMock()
    mem.retrieve.return_value = []

    res = build_context("test query", memory=mem, project_dir=str(tmp_path))
    assert "Repository Symbol Map" in res or "foo.py" in res
```

- [ ] **Step 2: Run test to verify it fails**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_context_repo_map.py`
Expected: FAIL or missing repo map.

- [ ] **Step 3: Update `agent/runtime/context.py`**

In `agent/runtime/context.py`:
Import `generate_repo_map` from `runtime.repo_map`. If `project_dir` is provided, generate symbol map and prepend to context sections.

- [ ] **Step 4: Run test to verify it passes**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_context_repo_map.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/context.py agent/tests/test_context_repo_map.py
git commit -m "feat(context): embed repository symbol map into context assembler"
```

---

### Task 3: Auto-Healing Retry Loop in Scheduler (`agent/runtime/scheduler.py`)

**Files**:
- Modify: `agent/runtime/scheduler.py`
- Test: `agent/tests/test_scheduler_auto_healing.py`

- [ ] **Step 1: Write failing test**

Create `agent/tests/test_scheduler_auto_healing.py`:
```python
from unittest.mock import MagicMock, patch
from runtime.scheduler import run_agent

@patch("runtime.scheduler.run_reviewer", return_value="APPROVED")
@patch("runtime.scheduler.validate")
@patch("runtime.scheduler.run_tool_agent")
def test_scheduler_passes_error_on_retry(mock_tool_agent, mock_validate, mock_reviewer, tmp_path):
    mock_tool_agent.return_value = "Fixed bug"
    
    val_fail = MagicMock()
    val_fail.passed = False
    val_fail.stage = "pytest"
    val_fail.errors = "AssertionError: expected 1 got 2"

    val_pass = MagicMock()
    val_pass.passed = True

    mock_validate.side_effect = [val_fail, val_pass]

    res = run_agent("Fix bug", project_dir=str(tmp_path))

    assert mock_tool_agent.call_count == 2
    second_call_arg = mock_tool_agent.call_args_list[1][0][0]
    assert "AssertionError" in second_call_arg
```

- [ ] **Step 2: Run test to verify it fails**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_scheduler_auto_healing.py`
Expected: FAIL.

- [ ] **Step 3: Update `agent/runtime/scheduler.py`**

In `agent/runtime/scheduler.py`:
When `last_error` is non-empty, pass `f"{task['description']}\n\nPrevious Failure Trace:\n{last_error}"` into `run_tool_agent()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_scheduler_auto_healing.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/scheduler.py agent/tests/test_scheduler_auto_healing.py
git commit -m "feat(scheduler): enable auto-healing test trace feedback on retries"
```
