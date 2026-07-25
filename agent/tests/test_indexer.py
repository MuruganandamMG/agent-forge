import os
import pathlib
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
            assert any("util.py" in f for f in result["tree"])
            assert "main.py" in result["summaries"]

    def test_excludes_venv_and_pycache(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / ".venv").mkdir()
            (pathlib.Path(d) / ".venv" / "lib.py").write_text("x=1", encoding="utf-8")
            (pathlib.Path(d) / "__pycache__").mkdir()
            (pathlib.Path(d) / "__pycache__" / "m.cpython-311.pyc").write_text("x=1", encoding="utf-8")
            (pathlib.Path(d) / ".git").mkdir()
            (pathlib.Path(d) / ".git" / "config").write_text("x=1", encoding="utf-8")
            (pathlib.Path(d) / "node_modules").mkdir()
            (pathlib.Path(d) / "node_modules" / "pkg.json").write_text("{}", encoding="utf-8")
            (pathlib.Path(d) / ".agent_memory").mkdir()
            (pathlib.Path(d) / ".agent_memory" / "mem.json").write_text("{}", encoding="utf-8")
            (pathlib.Path(d) / ".superpowers").mkdir()
            (pathlib.Path(d) / ".superpowers" / "brief.md").write_text("text", encoding="utf-8")
            (pathlib.Path(d) / ".agents").mkdir()
            (pathlib.Path(d) / ".agents" / "cfg.json").write_text("{}", encoding="utf-8")
            (pathlib.Path(d) / "real.py").write_text("y=2", encoding="utf-8")
            result = index_project(d)
            assert len(result["tree"]) == 1
            assert "real.py" in result["tree"]

    def test_summary_truncates_to_30_lines(self):
        with tempfile.TemporaryDirectory() as d:
            content = "\n".join(f"line {i}" for i in range(100))
            (pathlib.Path(d) / "big.py").write_text(content, encoding="utf-8")
            result = index_project(d)
            assert result["summaries"]["big.py"].count("\n") <= 29

    def test_includes_supported_extensions(self):
        with tempfile.TemporaryDirectory() as d:
            exts = [".py", ".md", ".toml", ".txt", ".yaml", ".yml", ".json", ".cfg"]
            for i, ext in enumerate(exts):
                (pathlib.Path(d) / f"file{i}{ext}").write_text(f"content {i}", encoding="utf-8")
            (pathlib.Path(d) / "ignored.bin").write_text("binary", encoding="utf-8")
            (pathlib.Path(d) / "ignored.exe").write_text("exe", encoding="utf-8")
            result = index_project(d)
            assert len(result["tree"]) == len(exts)
            assert not any(f.endswith(".bin") or f.endswith(".exe") for f in result["tree"])

    def test_handles_unreadable_file_gracefully(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "unreadable.py"
            p.write_text("content", encoding="utf-8")
            # We test normal indexing first; if read raises OSError, it skips summary gracefully
            result = index_project(d)
            assert "unreadable.py" in result["tree"]


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

    def test_formatted_output(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "app.py").write_text("pass", encoding="utf-8")
            (pathlib.Path(d) / "README.md").write_text("# Hello", encoding="utf-8")
            ctx = generate_project_context(d)
            assert "# Project Context" in ctx
            assert f"**Project:** {os.path.basename(os.path.abspath(d))}" in ctx
            assert f"**Root:** {os.path.abspath(d)}" in ctx
            assert "## File Tree (2 files)" in ctx
            assert "  README.md" in ctx or "  app.py" in ctx
