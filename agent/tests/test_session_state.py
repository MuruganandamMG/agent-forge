import json
import tempfile
from pathlib import Path

from runtime.session_state import (
    SessionState,
    load_session_state,
    print_resume_banner,
    save_session_state,
)


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
            assert loaded.pending_tasks == ["wire into main"]

    def test_load_missing_file_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as d:
            state = load_session_state(d)
            assert state.last_goal == ""
            assert state.completed_tasks == []

    def test_load_corrupt_json_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "session_state.json").write_text("not json!", encoding="utf-8")
            state = load_session_state(d)
            assert state.last_goal == ""

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            state = SessionState(last_goal="test")
            save_session_state(state, d)
            assert (Path(d) / "session_state.json").exists()

    def test_save_sets_last_run_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            state = SessionState(last_goal="test")
            save_session_state(state, d)
            loaded = load_session_state(d)
            assert loaded.last_run != ""

    def test_print_resume_banner_empty_goal(self, capsys):
        state = SessionState()
        print_resume_banner(state)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_resume_banner_with_data(self, capsys):
        state = SessionState(
            last_goal="fix gate",
            completed_tasks=["task 1", "task 2"],
            pending_tasks=["task 3"],
        )
        print_resume_banner(state)
        captured = capsys.readouterr()
        assert "fix gate" in captured.out
        assert "task 1" in captured.out
        assert "task 3" in captured.out

    def test_load_json_with_null_fields_returns_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            null_json = json.dumps({
                "last_run": None,
                "last_goal": None,
                "completed_tasks": None,
                "pending_tasks": None,
                "last_files_modified": None,
                "open_errors": None,
            })
            (Path(d) / "session_state.json").write_text(null_json, encoding="utf-8")
            state = load_session_state(d)
            assert state.last_run == ""
            assert state.last_goal == ""
            assert state.completed_tasks == []
            assert state.pending_tasks == []
            assert state.last_files_modified == []
            assert state.open_errors == []

