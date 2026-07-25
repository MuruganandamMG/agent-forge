# CLI Agent Next-Level Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CLI coding agent aware of the project it's working on, remember across sessions, and classify inputs intelligently using project context.

**Architecture:** Five upgrades applied sequentially — project indexer, session state persistence, LLM-assisted input classifier, request enricher, and session continuity banner. Each builds on the previous.

**Tech Stack:** Python 3.11, Qwen3-8B via llama-server, ChromaDB, click

## Global Constraints

- Python >=3.11, type hints on all public functions
- All new modules must have corresponding test files with ≥80% coverage of public API
- No new dependencies beyond what's in `requirements.txt`
- All 66+ existing tests must continue passing after each task
- `max_tokens` and `stop` sequences must be used on all new LLM calls
- Files must use UTF-8 encoding
- Windows-compatible paths (use `pathlib.Path`)
- Each task commits independently with a descriptive message

---

### Task 1: Project Indexer (`runtime/indexer.py`)

**Files:**
- Create: `runtime/indexer.py`
- Test: `tests/test_indexer.py`

**Interfaces:**
- Produces: `index_project(project_path: str) -> dict` returning `{"tree": list[str], "summaries": dict[str, str]}`
- Produces: `generate_project_context(project_path: str) -> str` returning a formatted markdown string suitable for injection into planner prompts

**Step-by-step:**

- [ ] **Step 1: Write failing tests for `index_project`**

```python
# tests/test_indexer.py
import os
import tempfile
from runtime.indexer import index_project, generate_project_context

class TestIndexProject:
    def test_indexes_python_files(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
            (pathlib.Path(d) / "sub").mkdir()
            (pathlib.Path(d) / "sub" / "util.py").write_text("x = 1\n", encoding="utf-8")
            result = index_project(d)
            assert "main.py" in result["tree"]
            assert "sub\\util.py" in result["tree"] or "sub/util.py" in result["tree"]
            assert "main.py" in result["summaries"]

    def test_excludes_venv_and_pycache(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / ".venv").mkdir()
            (pathlib.Path(d) / ".venv" / "lib.py").write_text("x=1", encoding="utf-8")
            (pathlib.Path(d) / "__pycache__").mkdir()
            (pathlib.Path(d) / "__pycache__" / "m.cpython-311.pyc").write_text("x=1", encoding="utf-8")
            (pathlib.Path(d) / "real.py").write_text("y=2", encoding="utf-8")
            result = index_project(d)
            assert len(result["tree"]) == 1
            assert "real.py" in result["tree"]

    def test_summary_truncates_to_30_lines(self):
        with tempfile.TemporaryDirectory() as d:
            content = "\n".join(f"line {i}" for i in range(100))
            (pathlib.Path(d) / "big.py").write_text(content, encoding="utf-8")
            result = index_project(d)
            assert result["summaries"]["big.py"].count("\n") <= 29  # 30 lines = 29 newlines

class TestGenerateProjectContext:
    def test_includes_file_tree(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "app.py").write_text("pass", encoding="utf-8")
            ctx = generate_project_context(d)
            assert "app.py" in ctx

    def test_includes_project_root(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "app.py").write_text("pass", encoding="utf-8")
            ctx = generate_project_context(d)
            assert d in ctx or os.path.basename(d) in ctx
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_indexer.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `runtime/indexer.py`**

```python
"""Project directory indexer for building static project context."""

import os
from pathlib import Path

INCLUDE_EXTENSIONS = {".py", ".md", ".toml", ".txt", ".yaml", ".yml", ".json", ".cfg"}
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", ".agent_memory", ".superpowers", ".agents"}


def index_project(project_path: str) -> dict:
    """Scan project directory and build a lightweight index.

    Returns:
        dict with keys:
            'tree': list of relative file paths
            'summaries': dict mapping relative path -> first 30 lines of content
    """
    tree: list[str] = []
    summaries: dict[str, str] = {}

    for root, dirs, files in os.walk(project_path):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS)
        for f in sorted(files):
            p = Path(root) / f
            if p.suffix in INCLUDE_EXTENSIONS:
                rel = str(p.relative_to(project_path))
                tree.append(rel)
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    summaries[rel] = "\n".join(content.splitlines()[:30])
                except OSError:
                    pass

    return {"tree": tree, "summaries": summaries}


def generate_project_context(project_path: str) -> str:
    """Generate a formatted markdown string of project context for prompt injection.

    Returns a string suitable for including in planner/executor system prompts.
    """
    index = index_project(project_path)
    project_name = Path(project_path).name
    lines = [
        f"# Project Context",
        f"",
        f"**Project:** {project_name}",
        f"**Root:** {project_path}",
        f"",
        f"## File Tree ({len(index['tree'])} files)",
        f"",
    ]
    for f in index["tree"]:
        lines.append(f"  {f}")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_indexer.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/indexer.py tests/test_indexer.py
git commit -m "feat: add project indexer module with directory scanning and context generation"
```

---

### Task 2: Wire Indexer into Startup & Planner (`runtime/main.py`, `runtime/scheduler.py`)

**Files:**
- Modify: `runtime/main.py`
- Modify: `runtime/scheduler.py`
- Test: `tests/test_scheduler.py` (extend existing)

**Interfaces:**
- Consumes: `generate_project_context(project_path: str) -> str` from `runtime/indexer.py`
- Consumes: `run_agent(user_query: str, project_dir: str, project_context: str = "") -> str`
- Modifies: `run_agent()` signature to accept `project_context` parameter
- Modifies: `_plan()` to include project context in planner messages
- Modifies: `_execute()` to include project context in executor messages

**Step-by-step:**

- [ ] **Step 1: Write failing test for project context injection**

```python
# Extend tests/test_scheduler.py
class TestProjectContextInjection:
    def test_plan_receives_project_context(self, mock_chat, tmp_path):
        """Verify _plan includes project context in messages when provided."""
        from runtime.scheduler import _plan
        mock_chat.return_value = '{"goal":"test","tasks":[]}'
        _plan("test query", context="## File Tree\n  main.py")
        call_args = mock_chat.call_args
        messages = call_args[0][0]
        assert any("File Tree" in m["content"] for m in messages)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Update `runtime/scheduler.py`**

Add `project_context` parameter to `run_agent()`, pass it through to `_plan()` and `_execute()`.

- [ ] **Step 4: Update `runtime/main.py`**

Call `generate_project_context(project_dir)` on startup, pass result to `run_agent()`.

```python
from runtime.indexer import generate_project_context

# After server startup, before REPL:
print("🔍 Indexing project...")
project_ctx = generate_project_context(project_dir)
print(f"📁 Indexed {project_ctx.count(chr(10))} entries")

# In REPL loop:
run_agent(query, project_dir, project_context=project_ctx)
```

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (66+ tests)

- [ ] **Step 6: Commit**

```bash
git add runtime/main.py runtime/scheduler.py tests/test_scheduler.py
git commit -m "feat: wire project indexer into startup and inject context into planner/executor"
```

---

### Task 3: Session State Persistence (`runtime/session_state.py`)

**Files:**
- Create: `runtime/session_state.py`
- Modify: `runtime/main.py`
- Test: `tests/test_session_state.py`

**Interfaces:**
- Produces: `SessionState` dataclass with `last_run`, `last_goal`, `completed_tasks`, `pending_tasks`, `last_files_modified`, `open_errors`
- Produces: `load_session_state(project_dir: str) -> SessionState`
- Produces: `save_session_state(state: SessionState, project_dir: str) -> None`
- Produces: `print_resume_banner(state: SessionState) -> None`

**Step-by-step:**

- [ ] **Step 1: Write failing tests**

```python
# tests/test_session_state.py
import json
import tempfile
from pathlib import Path
from runtime.session_state import SessionState, load_session_state, save_session_state


class TestSessionState:
    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            state = SessionState(
                last_goal="fix the gate",
                completed_tasks=["added gate.py"],
                pending_tasks=["wire into main"],
                last_files_modified=["runtime/gate.py"],
            )
            save_session_state(state, d)
            loaded = load_session_state(d)
            assert loaded.last_goal == "fix the gate"
            assert loaded.completed_tasks == ["added gate.py"]

    def test_load_missing_file_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as d:
            state = load_session_state(d)
            assert state.last_goal == ""
            assert state.completed_tasks == []

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            state = SessionState(last_goal="test")
            save_session_state(state, d)
            assert (Path(d) / "session_state.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement `runtime/session_state.py`**

```python
"""Session state persistence between agent runs."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class SessionState:
    last_run: str = ""
    last_goal: str = ""
    completed_tasks: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    last_files_modified: list[str] = field(default_factory=list)
    open_errors: list[str] = field(default_factory=list)


def load_session_state(project_dir: str) -> SessionState:
    path = Path(project_dir) / "session_state.json"
    if not path.exists():
        return SessionState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**{k: v for k, v in data.items() if k in SessionState.__dataclass_fields__})
    except (json.JSONDecodeError, TypeError):
        return SessionState()


def save_session_state(state: SessionState, project_dir: str) -> None:
    state.last_run = datetime.now(timezone.utc).isoformat()
    path = Path(project_dir) / "session_state.json"
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def print_resume_banner(state: SessionState) -> None:
    if not state.last_goal:
        return
    print(f"\n📋 Last session: {state.last_goal}")
    if state.completed_tasks:
        for t in state.completed_tasks[-3:]:
            print(f"   ✅ {t}")
    if state.pending_tasks:
        for t in state.pending_tasks[:3]:
            print(f"   ⏳ {t}")
    if state.open_errors:
        for e in state.open_errors[:2]:
            print(f"   ❌ {e}")
    print()
```

- [ ] **Step 4: Wire into `runtime/main.py`**

Load state on startup, print resume banner, save state after each REPL iteration.

- [ ] **Step 5: Run all tests**

- [ ] **Step 6: Commit**

```bash
git add runtime/session_state.py tests/test_session_state.py runtime/main.py
git commit -m "feat: add session state persistence with resume banner on startup"
```

---

### Task 4: LLM-Assisted Input Classifier (Stage 2 in `runtime/gate.py`)

**Files:**
- Create: `prompts/classifier_system.txt`
- Modify: `runtime/gate.py`
- Test: `tests/test_gate.py` (extend existing)

**Interfaces:**
- Consumes: `chat()` from `runtime/models.py`
- Consumes: project file tree from `index_project()` or `generate_project_context()`
- Produces: `llm_classify(text: str, project_context: str) -> str` returning `"TASK"`, `"VAGUE"`, or `"CHAT"`
- Modifies: `quick_classify()` unchanged (still Stage 1)
- Produces: `classify_input(text: str, project_context: str = "") -> str` — runs Stage 1, then Stage 2 only if ambiguous

**Step-by-step:**

- [ ] **Step 1: Create `prompts/classifier_system.txt`**

```
You are a task classifier for a coding assistant.
Classify the following user input as exactly one of:
- TASK: a clear, actionable coding request (create, fix, refactor, test, debug, etc.)
- VAGUE: needs more detail before the assistant can act
- CHAT: conversation, greeting, or non-coding discussion

Reply with exactly one word: TASK, VAGUE, or CHAT.
```

- [ ] **Step 2: Write failing tests**

```python
# Extend tests/test_gate.py
from unittest.mock import patch

class TestClassifyInput:
    def test_trivial_bypasses_llm(self):
        """Stage 1 catches trivial input, LLM is never called."""
        with patch("runtime.gate.chat") as mock_chat:
            result = classify_input("hello")
            mock_chat.assert_not_called()
            assert result == "trivial"

    def test_ambiguous_calls_llm(self):
        """Stage 1 returns 'task' for 'please help me with the codebase',
        but it's ambiguous enough that Stage 2 should be called."""
        with patch("runtime.gate.chat", return_value="VAGUE"):
            result = classify_input("please help me with the codebase", project_context="main.py")
            assert result == "vague"

    def test_clear_task_skips_llm(self):
        """Clear coding requests skip Stage 2."""
        with patch("runtime.gate.chat") as mock_chat:
            result = classify_input("fix error in runtime/scheduler.py")
            mock_chat.assert_not_called()
            assert result == "task"
```

- [ ] **Step 3: Implement `classify_input` in `runtime/gate.py`**

- [ ] **Step 4: Wire `classify_input` into `runtime/main.py`** (replacing `quick_classify` call)

- [ ] **Step 5: Run all tests**

- [ ] **Step 6: Commit**

```bash
git add prompts/classifier_system.txt runtime/gate.py tests/test_gate.py runtime/main.py
git commit -m "feat: add LLM-assisted Stage 2 input classifier with project context"
```

---

### Task 5: Request Enricher (`runtime/enricher.py`)

**Files:**
- Create: `runtime/enricher.py`
- Modify: `runtime/scheduler.py`
- Test: `tests/test_enricher.py`

**Interfaces:**
- Consumes: `chat()` from `runtime/models.py`
- Consumes: `index_project()` from `runtime/indexer.py`
- Consumes: `Memory.retrieve()` from `runtime/memory.py`
- Produces: `enrich_request(raw_query: str, project_context: str, memory: Memory | None = None) -> str`
- Returns enriched request string with file references, related files, and context

**Step-by-step:**

- [ ] **Step 1: Write failing tests**

```python
# tests/test_enricher.py
from unittest.mock import patch, MagicMock
from runtime.enricher import enrich_request


class TestEnrichRequest:
    def test_returns_enriched_string(self):
        with patch("runtime.enricher.chat", return_value="Files: runtime/scheduler.py\nContext: retry logic in _execute"):
            result = enrich_request("fix the retry loop", project_context="runtime/scheduler.py\nruntime/models.py")
            assert "scheduler" in result.lower() or "retry" in result.lower()

    def test_includes_raw_query(self):
        with patch("runtime.enricher.chat", return_value="Files: main.py"):
            result = enrich_request("add logging", project_context="main.py")
            assert "add logging" in result

    def test_handles_empty_context(self):
        with patch("runtime.enricher.chat", return_value="No specific files identified."):
            result = enrich_request("do something", project_context="")
            assert "do something" in result
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Implement `runtime/enricher.py`**

```python
"""Request enricher — adds file context and memory before planner receives the request."""

from pathlib import Path
from runtime.models import chat


def enrich_request(
    raw_query: str,
    project_context: str,
    memory_context: str = "",
) -> str:
    """Enrich a raw user request with file references and memory context.

    Calls the LLM to identify relevant files and recent context,
    then returns the enriched request for the planner.
    """
    system = (
        "You are a request enricher for a coding assistant. "
        "Given a user's coding request and the project file tree, "
        "identify which files are likely relevant, what related files might be affected, "
        "and any useful context. Be concise.\n\n"
        "Format your response as:\n"
        "Files: <comma-separated list of relevant files>\n"
        "Related: <comma-separated list of related files>\n"
        "Context: <one sentence of useful context>"
    )

    user_content = f"Request: {raw_query}\n\nProject files:\n{project_context}"
    if memory_context:
        user_content += f"\n\nRecent session context:\n{memory_context}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    enrichment = chat(messages, temperature=0.1, max_tokens=200, stop=["<|im_end|>"])

    return f"{raw_query}\n\n--- Enrichment ---\n{enrichment}"
```

- [ ] **Step 4: Wire into `runtime/scheduler.py`**

Call `enrich_request()` in `run_agent()` before `_plan()` or `_execute()`.

- [ ] **Step 5: Run all tests**

- [ ] **Step 6: Commit**

```bash
git add runtime/enricher.py tests/test_enricher.py runtime/scheduler.py
git commit -m "feat: add request enricher for file context injection before planner"
```

---

## Verification Plan

### Automated Tests
- `python -m pytest tests/test_indexer.py -v`
- `python -m pytest tests/test_session_state.py -v`
- `python -m pytest tests/test_gate.py -v`
- `python -m pytest tests/test_enricher.py -v`
- `python -m pytest tests/ -v` (full suite, 66+ all passing)

### Manual Verification
- Start agent, verify project index scan output appears
- Verify session state is saved after a query and resume banner shows on next run
- Test `hhmm` → instant trivial response (no LLM call)
- Test `fix the retry loop` → enriched request shows relevant files
