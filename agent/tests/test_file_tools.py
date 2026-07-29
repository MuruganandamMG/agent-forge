import os
import pytest
from runtime.tools.file_tools import read_file, edit_file, write_file, search, list_dir

def test_write_and_read_file(tmp_path):
    fpath = str(tmp_path / "test.txt")
    res_w = write_file(path=fpath, content="line1\nline2\nline3\n")
    assert res_w.success is True

    res_r = read_file(path=fpath, offset=1, limit=2)
    assert res_r.success is True
    assert "line1" in res_r.output
    assert "line2" in res_r.output

def test_edit_file(tmp_path):
    fpath = str(tmp_path / "code.py")
    write_file(path=fpath, content="def foo():\n    return 1\n")
    
    res_e = edit_file(path=fpath, old_text="return 1", new_text="return 42")
    assert res_e.success is True

    res_r = read_file(path=fpath)
    assert "return 42" in res_r.output

def test_search(tmp_path):
    fpath1 = str(tmp_path / "file1.txt")
    fpath2 = str(tmp_path / "file2.txt")
    write_file(path=fpath1, content="target_function_alpha()")
    write_file(path=fpath2, content="beta_function()")

    res_s = search(query="target_function", path=str(tmp_path))
    assert res_s.success is True
    assert "file1.txt" in res_s.output
    assert "target_function_alpha" in res_s.output

def test_list_dir(tmp_path):
    write_file(path=str(tmp_path / "a.txt"), content="a")
    write_file(path=str(tmp_path / "b.txt"), content="b")

    res_l = list_dir(path=str(tmp_path))
    assert res_l.success is True
    assert "a.txt" in res_l.output
    assert "b.txt" in res_l.output
