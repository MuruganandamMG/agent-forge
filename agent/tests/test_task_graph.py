import json

import pytest

from runtime.task_graph import TaskGraph


class TestFromPlanJson:
    def test_parses_valid_plan(self) -> None:
        plan_json = json.dumps({
            "goal": "Add a hello function",
            "tasks": [
                {
                    "id": 1,
                    "description": "Create hello.py",
                    "files": ["hello.py"],
                    "depends_on": [],
                },
                {
                    "id": 2,
                    "description": "Add tests",
                    "files": ["tests/test_hello.py"],
                    "depends_on": [1],
                },
            ],
        })
        tg = TaskGraph.from_plan_json(plan_json)
        assert tg.goal == "Add a hello function"
        assert len(tg.tasks) == 2

    def test_strips_markdown_fences(self) -> None:
        plan_json = '```json\n{"goal": "test", "tasks": []}\n```'
        tg = TaskGraph.from_plan_json(plan_json)
        assert tg.goal == "test"

    def test_rejects_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="is not a valid JSON object"):
            TaskGraph.from_plan_json("not json at all")


class TestTaskIteration:
    def _make_graph(self) -> TaskGraph:
        plan_json = json.dumps({
            "goal": "test",
            "tasks": [
                {"id": 1, "description": "first", "files": [], "depends_on": []},
                {"id": 2, "description": "second", "files": [], "depends_on": []},
            ],
        })
        return TaskGraph.from_plan_json(plan_json)

    def test_next_task_returns_first_incomplete(self) -> None:
        tg = self._make_graph()
        task = tg.next_task()
        assert task is not None
        assert task["id"] == 1

    def test_mark_done_advances(self) -> None:
        tg = self._make_graph()
        tg.mark_done(1)
        task = tg.next_task()
        assert task is not None
        assert task["id"] == 2

    def test_all_done_returns_none(self) -> None:
        tg = self._make_graph()
        tg.mark_done(1)
        tg.mark_done(2)
        assert tg.next_task() is None

    def test_mark_failed_records_reason(self) -> None:
        tg = self._make_graph()
        tg.mark_failed(1, "validation error")
        assert tg.tasks[0]["status"] == "failed"
        assert tg.tasks[0]["failure_reason"] == "validation error"

    def test_mark_done_unknown_id_raises(self) -> None:
        tg = self._make_graph()
        with pytest.raises(KeyError, match="Task 99 not found"):
            tg.mark_done(99)


class TestSummary:
    def test_summary_contains_goal(self) -> None:
        plan_json = json.dumps({
            "goal": "Build a widget",
            "tasks": [{"id": 1, "description": "step one", "files": [], "depends_on": []}],
        })
        tg = TaskGraph.from_plan_json(plan_json)
        summary = tg.summary()
        assert "Build a widget" in summary
        assert "⬜" in summary  # pending icon

    def test_summary_shows_failure_reason(self) -> None:
        plan_json = json.dumps({
            "goal": "test",
            "tasks": [{"id": 1, "description": "fail", "files": [], "depends_on": []}],
        })
        tg = TaskGraph.from_plan_json(plan_json)
        tg.mark_failed(1, "broke everything")
        summary = tg.summary()
        assert "❌" in summary
        assert "broke everything" in summary
