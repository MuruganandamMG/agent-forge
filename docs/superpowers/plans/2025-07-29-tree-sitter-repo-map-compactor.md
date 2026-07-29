# Implementation Plan: Sub-Project 3 (Tree-Sitter Repo Mapping & Context Auto-Compactor)

This plan details the implementation of structural repository symbol mapping (`repo_map.py`) and dynamic context summarization/compactor (`compactor.py`) for `agent-forge`.

---

## Proposed Plan

### Task 1: Repository Symbol Mapper (`agent/runtime/repo_map.py`)
- **Files**:
  - `agent/runtime/repo_map.py`
  - `agent/tests/test_repo_map.py`
- **Implementation**:
  - Implement `generate_repo_map(project_dir: str) -> str`.
  - Parses `.py` files using `ast` (with fallback regex/tree-sitter integration) to map top-level classes, functions, and docstrings into a single unified skeleton map.
- **Verification**:
  - Run `pytest agent/tests/test_repo_map.py`.

### Task 2: Context Auto-Compactor (`agent/runtime/compactor.py`)
- **Files**:
  - `agent/runtime/compactor.py`
  - `agent/tests/test_compactor.py`
- **Implementation**:
  - Implement `compact_context(messages: list[dict], max_tokens: int) -> list[dict]`.
  - Automatically collapses older tool responses or message turns into concise summaries when total token budget is exceeded.
- **Verification**:
  - Run `pytest agent/tests/test_compactor.py`.

---

## Final Verification Checklist
- Run `pytest agent/tests/test_repo_map.py agent/tests/test_compactor.py`.
- Verify git status clean and commit changes.
