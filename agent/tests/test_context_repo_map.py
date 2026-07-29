from unittest.mock import MagicMock
from runtime.context import build_context

def test_build_context_includes_repo_map(tmp_path):
    f = tmp_path / "foo.py"
    f.write_text("def my_func(): pass", encoding="utf-8")

    mem = MagicMock()
    mem.retrieve.return_value = []

    res = build_context("test query", memory=mem, project_dir=str(tmp_path))
    assert "Repository Symbol Map" in res or "foo.py" in res
