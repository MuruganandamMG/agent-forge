# Claude Code / Codex CLI Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the autonomous tool agent loop (`run_tool_agent`) as the default task execution engine across `scheduler.py`, `run.py`, and `chat.py` with real-time tool execution rendering.

**Architecture:** Connect `run_tool_agent` with standard file and shell tools (`read_file`, `edit_file`, `write_file`, `search`, `list_dir`, `bash`) into `run_agent()` in `scheduler.py`. Render tool calls dynamically in terminal using Rich console panels.

**Tech Stack:** Python 3.13, Click, Rich, Google GenAI SDK (`gemini-2.5-pro`).

## Global Constraints
- Unified test suite via `pytest`.
- Offline testing capability using `GEMINI_API_KEY=dummy_key` and mock provider responses.

---

### Task 1: Integrate Tool Agent Execution into Scheduler Core (`agent/runtime/scheduler.py`)

**Files**:
- Modify: `agent/runtime/scheduler.py`
- Test: `agent/tests/test_scheduler_tool_agent.py`

**Interfaces**:
- Consumes: `run_tool_agent` from `agent/runtime/subagents/tool_agent.py`
- Produces: `run_agent` executing tasks via tool calls with fallback and git checkpointing.

- [ ] **Step 1: Write failing test**

Create `agent/tests/test_scheduler_tool_agent.py`:
```python
from unittest.mock import MagicMock, patch
from runtime.scheduler import run_agent

@patch("runtime.scheduler.run_tool_agent")
def test_run_agent_uses_tool_agent(mock_tool_agent, tmp_path):
    mock_tool_agent.return_value = "Task completed with tools"

    res = run_agent("Fix bug in main.py", project_dir=str(tmp_path))

    mock_tool_agent.assert_called_once()
    assert res.raw == "Task completed with tools"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_scheduler_tool_agent.py`
Expected: FAIL (because `run_agent` does not yet call `run_tool_agent`).

- [ ] **Step 3: Update `scheduler.py` implementation**

In `agent/runtime/scheduler.py`:
Replace `run_implementer` diff generation step with `run_tool_agent(task['description'])`.

- [ ] **Step 4: Run test to verify it passes**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_scheduler_tool_agent.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/scheduler.py agent/tests/test_scheduler_tool_agent.py
git commit -m "feat(scheduler): switch task execution engine to autonomous tool agent loop"
```

---

### Task 2: Live Tool Call Rendering in Subagent Runner (`agent/runtime/subagents/tool_agent.py`)

**Files**:
- Modify: `agent/runtime/subagents/tool_agent.py`
- Test: `agent/tests/test_tool_agent_rendering.py`

**Interfaces**:
- Consumes: `render_subagent_card` from `agent/runtime/ui.py`
- Produces: Rich terminal output for each invoked tool call during execution loop.

- [ ] **Step 1: Write failing test**

Create `agent/tests/test_tool_agent_rendering.py`:
```python
from unittest.mock import MagicMock, patch
from runtime.subagents.tool_agent import run_tool_agent
from runtime.tools.base import Tool, tool

@tool(description="Mock tool for rendering test")
def mock_render_tool(msg: str) -> str:
    return f"Processed {msg}"

@patch("runtime.subagents.tool_agent.render_subagent_card")
def test_tool_agent_renders_tool_cards(mock_render, tmp_path):
    provider_mock = MagicMock()
    call_mock = MagicMock()
    call_mock.name = "mock_render_tool"
    call_mock.args = {"msg": "hello"}

    provider_mock.chat_with_tools.side_effect = [
        ("Calling tool", [call_mock]),
        ("Done", None)
    ]

    run_tool_agent("Test task", tools=[Tool(mock_render_tool)], provider=provider_mock, max_turns=2)
    mock_render.assert_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_tool_agent_rendering.py`
Expected: FAIL.

- [ ] **Step 3: Update `tool_agent.py` to call `render_subagent_card`**

In `agent/runtime/subagents/tool_agent.py`:
Import `render_subagent_card` from `runtime.ui`. Before executing each tool call, render a tool invocation card with `render_subagent_card(f"🛠️ Executing Tool: {tool_name}", str(tool_args), border_style="blue")`.

- [ ] **Step 4: Run test to verify it passes**

Run: `GEMINI_API_KEY=dummy_key pytest agent/tests/test_tool_agent_rendering.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/subagents/tool_agent.py agent/tests/test_tool_agent_rendering.py
git commit -m "feat(subagents): add live Rich rendering for tool execution calls"
```
