# God-Mode CLI UI & Context Window Telemetry Design Spec

**Date:** 2025-07-26
**Topic:** God-Mode CLI UI with Context Window Telemetry & Stepper Cards
**Status:** Approved

---

## 1. Goal & Overview

Transform `agent-forge`'s CLI output into a high-octane "God-Mode" terminal experience. The design retains 100% linear terminal scrollback while introducing:
- A Cyberpunk neon visual style with glowing borders, badges, and ASCII banners.
- Centralized UI Manager (`agent/runtime/ui.py`) managing themes, console output, and telemetry tracking.
- Context Window Telemetry tracking total prompt/generation tokens, model capacity limits (e.g. 128,000 for `gemini-2.5-pro`), usage percentages, and dynamic colored capacity gauges.
- Animated Pipeline Steppers & Subagent Callout Cards for direct visual feedback during scheduler execution.
- Interactive Power-REPL prompt with slash command formatting and telemetry status bars.

---

## 2. Architecture & File Decomposition

### Modified Files:
1. `agent/runtime/ui.py`:
   - Refactor into a comprehensive `UIManager` class with convenience module functions.
   - Theme definitions (`CYBERPUNK` palette: Magenta `#bd00ff`, Cyan `#00f0ff`, Green `#00ff66`, Amber `#ff9900`, Red `#ff0055`).
   - `render_ascii_banner(model, project_dir, file_count, context_used, context_limit)` function.
   - `render_context_gauge(used_tokens, limit_tokens)` generating `[████████░░] 38% (48.6k / 128k tokens)` with dynamic colors.
   - `render_task_header(task_id, total_tasks, goal, files)`.
   - `render_step(step_num, total_steps, name, status, detail)`.
   - `render_subagent_card(title, content, border_style, stats)`.
   - `render_summary_card(goal, completed, failed, files_modified, tokens_used, elapsed_sec)`.

2. `agent/runtime/scheduler.py`:
   - Replace generic `console.print` statements with structured calls to `UIManager`.
   - Track per-step timing and cumulative token usage across subagent calls (Planner, Implementer, Reviewer).
   - Display linear animated steppers for the 7 pipeline stages.
   - Render Implementer unified diffs inside syntax-highlighted callout cards with line stats (`+X / -Y`).
   - Render Reviewer Subagent critiques in styled boxed panels.

3. `agent/cli/chat.py`:
   - Display God-Mode startup ASCII header with live context window meter.
   - Update prompt input to `⚡ god-mode [gemini-2.5-pro] ❯ `.
   - Print context window usage badge after every response.
   - Format assistant chat responses in styled Markdown panels.

4. `agent/cli/run.py`:
   - Display God-Mode startup ASCII header.
   - Wrap task execution in `UIManager` task panels and pipeline steppers.
   - Output summary telemetry upon completion.

5. `agent/cli/status.py`:
   - Render session status using Rich tables and tree nodes with glowing theme colors.
   - Show context window usage stats, last goal, completed tasks, open errors, and modified files.

---

## 3. Detailed Component Specifications

### 3.1 Context Window Telemetry Calculator
```python
def format_context_gauge(used_tokens: int, limit_tokens: int = 128000, width: int = 20) -> str:
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
```

### 3.2 God-Mode ASCII Header
```
 ⚡ ╔═══════════════════════════════════════════════════════════════════════════╗ ⚡
 ⚡ ║   ___   ____ _____ _   _ _____   _____ ____  ____   ____ _____           ║ ⚡
 ⚡ ║  / _ \ / ___| ____| \ | |_   _| |  ___/ __ \|  _ \ / ___| ____|          ║ ⚡
 ⚡ ║ | |_| | |  _|  _| |  \| | | |   | |_ | |  | | |_) | |  _|  _|            ║ ⚡
 ⚡ ║ |  _  | |_| | |___| |\  | | |   |  _|| |__| |  _ <| |_| | |___           ║ ⚡
 ⚡ ║ |_| |_|\____|_____|_| \_| |_|   |_|   \____/|_| \_\\____|_____|          ║ ⚡
 ⚡ ║                                                                           ║ ⚡
 ⚡ ║  Model: gemini-2.5-pro  │  Branch: main  │  Files: 42 indexed           ║ ⚡
 ⚡ ║  Context Window: [██████████░░░░░░░░░░] 34% (43,520 / 128,000 tokens)      ║ ⚡
 ⚡ ╚═══════════════════════════════════════════════════════════════════════════╝ ⚡
```

### 3.3 Pipeline Stepper Output
```
┌─ ⚡ [TASK 1/2] ─────────────────────────────────────────────────────────────┐
│ Goal: Fix executor empty output on conversational query                     │
│ Target Files: agent/runtime/chat_responder.py                              │
└────────────────────────────────────────────────────────────────────────────┘

  [✓] 1/7 Classifier Gate ... [TASK]
  [✓] 2/7 Request Enricher ... Context assembled (2.4k tokens)
  [✓] 3/7 Planner Subagent ... Generated 1 task
  [⏳] 4/7 Implementer Subagent ... Generating diff (Attempt 1/3)
  [✓] 5/7 Sandbox ... Applied diff (+18, -2)
  [✓] 6/7 Validator ... Pytest passed (24 tests)
  [✓] 7/7 Reviewer Subagent ... APPROVED (Commit 3f8a12b)

  ✨ Task 1 Complete (1.8s | 14,200 tokens used)
```

---

## 4. Testing & Verification

1. Unit tests in `tests/test_ui.py`:
   - Test `format_context_gauge` formatting for 0%, 50%, 85%, and >100% token usage.
   - Test `render_ascii_banner` output generation.
   - Test `UIManager` telemetry recording (tokens, step count, timing).
2. Existing test suite verification (`pytest`):
   - Ensure changes to `ui.py`, `scheduler.py`, `chat.py`, `run.py`, and `status.py` break no existing functional tests.
3. Manual CLI verification:
   - Run `agent status`, `agent run "test query"`, and `agent chat` to verify visual rendering.

---

## 5. Self-Review Checklist

- [x] Spec coverage: Touches `ui.py`, `scheduler.py`, `chat.py`, `run.py`, `status.py`, and tests.
- [x] Placeholder scan: Zero placeholders or TODOs.
- [x] Type consistency: All types explicitly annotated (`int`, `str`, `dict`, `UIManager`).
- [x] Scope: Focused strictly on CLI UI, themes, steppers, cards, and context window telemetry.
