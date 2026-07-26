# Subagent Delegation Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the monolithic execution loop in `scheduler.py` into a dynamic multi-agent orchestrator natively utilizing Gemini to maintain and direct specialized subagents without requiring explicit user permission per subagent.

**Architecture:** 
1. Introduce a `subagents/` directory with persona-specific prompts/logic (`planner.py`, `implementer.py`, `reviewer.py`).
2. Implement a `Controller` within `scheduler.py` that automatically delegates work through a structured pipeline: `Planner -> Implementer -> Reviewer`.
3. The system will use the existing `models.chat()` method, connecting directly to Gemini. The user will not be prompted to authorize subagent calls—it will happen seamlessly in the background during `run_agent()`. Conversational chats will bypass this entirely.

**Tech Stack:** Python 3, `google-genai` (via `models.py`), `rich`

## Global Constraints

- Standard unified git diff format (`diff -u`) for patches.
- All code goes in `E:/AI/Models/agent-forge/agent/`.
- No user prompts for continuing to the next subagent; fully autonomous pipeline.

---

### Task 1: Create Subagent Base and Specialized Prompts

**Files:**
- Create: `agent/runtime/subagents/__init__.py`
- Create: `agent/runtime/subagents/prompts.py`
- Create: `agent/tests/test_subagent_prompts.py`

**Interfaces:**
- Produces: `PLANNER_PROMPT`, `IMPLEMENTER_PROMPT`, `REVIEWER_PROMPT` string constants tailored for the respective agent personas.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from runtime.subagents.prompts import PLANNER_PROMPT, IMPLEMENTER_PROMPT, REVIEWER_PROMPT

def test_prompts_exist_and_are_strings():
    assert isinstance(PLANNER_PROMPT, str)
    assert isinstance(IMPLEMENTER_PROMPT, str)
    assert isinstance(REVIEWER_PROMPT, str)
    assert "plan" in PLANNER_PROMPT.lower()
    assert "diff" in IMPLEMENTER_PROMPT.lower()
    assert "review" in REVIEWER_PROMPT.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_subagent_prompts.py -v`
Expected: FAIL (missing module)

- [ ] **Step 3: Write implementation in `agent/runtime/subagents/prompts.py`**

```python
PLANNER_PROMPT = """You are the Forge Planner Subagent.
Given a user query and project context, break the goal down into a JSON array of specific tasks.
Return ONLY valid JSON.
Format:
{
  "goal": "Description of overall goal",
  "tasks": [
    {"id": 1, "description": "Task 1 description", "files": ["file1.py"]}
  ]
}
"""

IMPLEMENTER_PROMPT = """You are the Forge Implementer Subagent.
Given a task description and file contents, generate the code changes required to complete the task.
Output your changes EXCLUSIVELY as a unified git diff. Do not wrap the diff in markdown blocks.
"""

REVIEWER_PROMPT = """You are the Forge Reviewer Subagent.
Given a task description and a proposed git diff, evaluate if the diff correctly implements the task.
If it is perfect, return EXACTLY the word "APPROVED".
If there are errors, bugs, or missing requirements, return "REJECTED:" followed by a detailed list of corrections.
"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agent/tests/test_subagent_prompts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/subagents/ agent/tests/test_subagent_prompts.py
git commit -m "feat: add specialized subagent persona prompts"
```

---

### Task 2: Implement the Subagent Handlers

**Files:**
- Create: `agent/runtime/subagents/core.py`
- Create: `agent/tests/test_subagent_core.py`

**Interfaces:**
- Consumes: `chat` from `runtime.models`, `prompts.py`
- Produces: `run_planner`, `run_implementer`, `run_reviewer` functions.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch
from runtime.subagents.core import run_planner, run_implementer, run_reviewer

@patch("runtime.subagents.core.chat")
def test_subagent_handlers(mock_chat):
    mock_chat.return_value = "APPROVED"
    assert run_reviewer("task", "diff") == "APPROVED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agent/tests/test_subagent_core.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation in `agent/runtime/subagents/core.py`**

```python
import json
from runtime.models import chat
from runtime.subagents.prompts import PLANNER_PROMPT, IMPLEMENTER_PROMPT, REVIEWER_PROMPT

def run_planner(query: str, project_context: str) -> str:
    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": f"Context:\n{project_context}\n\nQuery:\n{query}"}
    ]
    return chat(messages, temperature=0.2)

def run_implementer(task_desc: str, file_contents: str, feedback: str = "") -> str:
    user_msg = f"Task:\n{task_desc}\n\nFiles:\n{file_contents}"
    if feedback:
        user_msg += f"\n\nPrevious Reviewer Feedback:\n{feedback}\nPlease fix these issues."
        
    messages = [
        {"role": "system", "content": IMPLEMENTER_PROMPT},
        {"role": "user", "content": user_msg}
    ]
    return chat(messages, temperature=0.1, max_tokens=4000)

def run_reviewer(task_desc: str, diff: str) -> str:
    messages = [
        {"role": "system", "content": REVIEWER_PROMPT},
        {"role": "user", "content": f"Task:\n{task_desc}\n\nProposed Diff:\n{diff}"}
    ]
    return chat(messages, temperature=0.1).strip()
```

- [ ] **Step 4: Run tests**

Run: `pytest agent/tests/test_subagent_core.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime/subagents/core.py agent/tests/test_subagent_core.py
git commit -m "feat: add discrete subagent invocation handlers"
```

---

### Task 3: Overhaul the Controller (`scheduler.py`)

**Files:**
- Modify: `agent/runtime/scheduler.py`
- Modify: `agent/tests/test_scheduler.py`

**Interfaces:**
- Consumes: `run_planner`, `run_implementer`, `run_reviewer` from `subagents/core.py`.
- Architecture: Replace the old `_execute` and validation human-in-the-loop with the seamless `Implementer -> Reviewer` auto-loop.

- [ ] **Step 1: Rewrite `scheduler.py` to use Subagents**

Replace `_plan` and `_execute` usage with the new subagent imports. Implement an inner loop inside `run_agent` that iterates up to 3 times per task: getting a diff from the `Implementer`, passing it to the `Reviewer`, and if `APPROVED`, applying it.

```python
# Refactor `run_agent` inside agent/runtime/scheduler.py
# (Full implementation details inside actual step execution, focusing on auto-approval logic)

# Replace the input("Apply this change? [y/n]") block with:
#
# reviewer_status = run_reviewer(task["description"], diff)
# if reviewer_status == "APPROVED":
#     sandbox.apply_diff(diff)
#     sandbox.checkpoint(task["description"])
#     ... break to next task
# else:
#     last_error = reviewer_status # loop back to implementer with this feedback
```

- [ ] **Step 2: Update Tests**
Adjust `test_scheduler.py` to mock `run_implementer` and `run_reviewer` instead of `_execute` and `chat`.

- [ ] **Step 3: Run tests**
`pytest agent/tests/ -v`

- [ ] **Step 4: Commit**
```bash
git add agent/runtime/scheduler.py agent/tests/test_scheduler.py
git commit -m "refactor: upgrade scheduler to fully autonomous subagent delegator"
```
