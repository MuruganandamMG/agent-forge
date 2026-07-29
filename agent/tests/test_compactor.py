import pytest
from runtime.compactor import compact_context, estimate_tokens

def test_estimate_tokens():
    text = "hello world" * 10
    tokens = estimate_tokens(text)
    assert tokens > 0

def test_compact_context_under_budget():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Fix bug in main.py"}
    ]
    compacted = compact_context(messages, max_tokens=1000)
    assert len(compacted) == 2
    assert compacted[0]["content"] == "You are a helpful assistant."

def test_compact_context_over_budget_compactor():
    verbose_turn = "x" * 10000
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Start task"},
        {"role": "assistant", "content": f"Large tool response: {verbose_turn}"},
        {"role": "user", "content": "Next step"}
    ]

    compacted = compact_context(messages, max_tokens=500)
    assert len(compacted) < len(messages) or "truncated" in str(compacted) or "summary" in str(compacted)
