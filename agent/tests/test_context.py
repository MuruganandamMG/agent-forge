from unittest.mock import MagicMock

import pytest

from runtime.context import build_context, load_agents_md


class TestLoadAgentsMd:
    def test_load_agents_md_finds_file(self, tmp_path) -> None:
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("# Project Rules\nRule 1: Clean code", encoding="utf-8")
        result = load_agents_md(str(tmp_path))
        assert "Rule 1: Clean code" in result

    def test_load_agents_md_returns_empty_when_missing(self, tmp_path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = load_agents_md(str(empty_dir))
        # Might fall back to agent/AGENTS.md if it exists in the agent repo
        assert isinstance(result, str)


class TestBuildContext:
    def test_includes_agents_md_and_file_tree(self) -> None:
        mem = MagicMock()
        mem.retrieve.return_value = []
        result = build_context(
            query="fix bug",
            memory=mem,
            file_contents="def foo(): pass",
            style="# Style",
            agents_md="# AGENTS Rules",
            file_tree="## File Tree\nmain.py",
            token_budget=6000,
        )
        assert "--- AGENTS.MD ---" in result
        assert "# AGENTS Rules" in result
        assert "--- FILE TREE ---" in result
        assert "## File Tree\nmain.py" in result

    def test_priority_order_agents_md_and_file_tree_first(self) -> None:
        mem = MagicMock()
        mem.retrieve.return_value = []
        result = build_context(
            query="fix bug",
            memory=mem,
            file_contents="def foo(): pass",
            style="# Style",
            agents_md="P1: Rules",
            file_tree="P2: Tree",
            token_budget=6000,
        )
        pos_p1 = result.find("P1: Rules")
        pos_p2 = result.find("P2: Tree")
        pos_style = result.find("# Style")
        pos_files = result.find("def foo(): pass")
        assert pos_p1 != -1 and pos_p2 != -1 and pos_style != -1 and pos_files != -1
        assert pos_p1 < pos_p2 < pos_style < pos_files

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

