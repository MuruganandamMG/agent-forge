from unittest.mock import MagicMock

import pytest

from runtime.context import build_context


class TestBuildContext:
    def test_always_includes_style(self) -> None:
        mem = MagicMock()
        mem.retrieve.return_value = []
        result = build_context(
            query="fix a bug",
            memory=mem,
            file_contents="def foo(): pass",
            style="# Use snake_case",
            token_budget=6000,
        )
        assert "# Use snake_case" in result

    def test_includes_file_contents(self) -> None:
        mem = MagicMock()
        mem.retrieve.return_value = []
        result = build_context(
            query="fix a bug",
            memory=mem,
            file_contents="def foo(): pass",
            style="",
            token_budget=6000,
        )
        assert "def foo(): pass" in result

    def test_includes_memory_results(self) -> None:
        mem = MagicMock()
        mem.retrieve.return_value = [
            {"document": "Previous: fixed import cycle by moving types"}
        ]
        result = build_context(
            query="fix import issue",
            memory=mem,
            file_contents="",
            style="",
            token_budget=6000,
        )
        assert "fixed import cycle" in result

    def test_truncates_to_budget(self) -> None:
        mem = MagicMock()
        mem.retrieve.return_value = [{"document": "x" * 50000}]
        result = build_context(
            query="test",
            memory=mem,
            file_contents="y" * 50000,
            style="z" * 1000,
            token_budget=2000,  # ~8000 chars
        )
        # Should be roughly within budget (4 chars per token heuristic)
        assert len(result) <= 2000 * 4 + 500
        assert "truncated to fit token budget" in result
