import pytest
from runtime.repo_map import generate_repo_map

def test_generate_repo_map_python_files(tmp_path):
    f1 = tmp_path / "module_a.py"
    f1.write_text("class Calculator:\n    def add(self, a, b):\n        return a + b\n\ndef helper():\n    pass\n", encoding="utf-8")

    f2 = tmp_path / "module_b.py"
    f2.write_text("def run():\n    pass\n", encoding="utf-8")

    repo_map = generate_repo_map(str(tmp_path))

    assert "module_a.py" in repo_map
    assert "class Calculator" in repo_map
    assert "def add" in repo_map
    assert "def helper" in repo_map
    assert "module_b.py" in repo_map
    assert "def run" in repo_map
