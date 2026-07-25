import pytest
from collections.abc import Callable
from pathlib import Path

from runtime.tools import (
    TOOLS,
    grep_search,
    list_dir,
    read_file,
    run_command,
)


class TestReadFile:
    def test_read_existing_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "sample.txt"
        file_path.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
        content = read_file(str(file_path))
        assert content == "line 1\nline 2\nline 3\n"

    def test_read_line_range(self, tmp_path: Path) -> None:
        file_path = tmp_path / "sample.txt"
        file_path.write_text("line 1\nline 2\nline 3\nline 4\n", encoding="utf-8")
        content = read_file(str(file_path), start_line=2, end_line=3)
        assert content == "line 2\nline 3\n"

    def test_read_nonexistent_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            read_file(str(file_path))


class TestListDir:
    def test_list_dir_contents(self, tmp_path: Path) -> None:
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        file_path = tmp_path / "file.txt"
        file_path.write_text("hello", encoding="utf-8")

        items = list_dir(str(tmp_path))
        assert len(items) == 2

        items_by_name = {item["name"]: item for item in items}
        assert "subdir" in items_by_name
        assert items_by_name["subdir"]["is_dir"] is True
        assert items_by_name["subdir"]["size"] is None

        assert "file.txt" in items_by_name
        assert items_by_name["file.txt"]["is_dir"] is False
        assert items_by_name["file.txt"]["size"] == 5

    def test_list_nonexistent_dir(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "nodir"
        with pytest.raises(NotADirectoryError):
            list_dir(str(nonexistent))


class TestGrepSearch:
    def test_grep_search_pattern(self, tmp_path: Path) -> None:
        file1 = tmp_path / "a.py"
        file1.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
        file2 = tmp_path / "b.py"
        file2.write_text("def foo():\n    hello()\n", encoding="utf-8")

        results = grep_search(pattern=r"def \w+\(\)", path=str(tmp_path))
        assert len(results) == 2

    def test_grep_search_case_insensitive(self, tmp_path: Path) -> None:
        file1 = tmp_path / "test.txt"
        file1.write_text("Hello World\nhello world\n", encoding="utf-8")

        results_sensitive = grep_search(pattern="Hello", path=str(tmp_path), case_insensitive=False)
        assert len(results_sensitive) == 1

        results_insensitive = grep_search(pattern="Hello", path=str(tmp_path), case_insensitive=True)
        assert len(results_insensitive) == 2


class TestRunCommand:
    def test_run_command_echo(self) -> None:
        res = run_command("echo Hello Sandbox")
        assert res["returncode"] == 0
        assert "Hello Sandbox" in res["stdout"]

    def test_run_command_timeout(self) -> None:
        res = run_command("ping -n 100 127.0.0.1", timeout=1)
        assert res["returncode"] != 0 or "timed out" in res["stderr"].lower()


class TestToolRegistry:
    def test_tools_dictionary(self) -> None:
        assert isinstance(TOOLS, dict)
        expected_keys = {"read_file", "list_dir", "grep_search", "run_command"}
        assert set(TOOLS.keys()) == expected_keys
        for name, func in TOOLS.items():
            assert isinstance(func, Callable)
