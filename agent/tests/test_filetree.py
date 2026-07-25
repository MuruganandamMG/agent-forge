import pathlib
import tempfile
from runtime.filetree import generate_filetree, IGNORED_DIRS


class TestGenerateFiletree:
    def test_basic_filetree_nested_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = pathlib.Path(tmp_dir)
            (base / "b_file.py").write_text("print('b')", encoding="utf-8")
            (base / "a_file.txt").write_text("hello", encoding="utf-8")
            (base / "sub").mkdir()
            (base / "sub" / "c_file.json").write_text("{}", encoding="utf-8")

            result = generate_filetree(tmp_dir)
            lines = result.splitlines()

            assert lines[0] == "## File Tree"
            # Paths should be sorted relative paths
            assert lines[1:] == ["a_file.txt", "b_file.py", "sub/c_file.json"]

    def test_ignores_specified_directories(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = pathlib.Path(tmp_dir)
            # Create a valid file
            (base / "valid.py").write_text("pass", encoding="utf-8")

            # Create files in every ignored directory
            for ignored in IGNORED_DIRS:
                ignored_dir = base / ignored
                ignored_dir.mkdir(parents=True, exist_ok=True)
                (ignored_dir / "ignored_file.txt").write_text("data", encoding="utf-8")

            result = generate_filetree(tmp_dir)
            lines = result.splitlines()

            assert lines[0] == "## File Tree"
            assert lines[1:] == ["valid.py"]

    def test_max_files_limit(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = pathlib.Path(tmp_dir)
            for i in range(10):
                (base / f"file_{i:02d}.txt").write_text(f"content {i}", encoding="utf-8")

            result = generate_filetree(tmp_dir, max_files=5)
            lines = result.splitlines()

            assert lines[0] == "## File Tree"
            assert len(lines[1:]) == 5
            assert lines[1:] == [f"file_{i:02d}.txt" for i in range(5)]

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_filetree(tmp_dir)
            assert result == "## File Tree"
