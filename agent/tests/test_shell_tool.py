import pytest
from runtime.tools.shell_tool import bash

def test_bash_simple_command():
    res = bash(command="echo Hello World")
    assert res.success is True
    assert "Hello World" in res.output

def test_bash_command_error():
    res = bash(command="non_existent_command_12345")
    assert res.success is False
    assert res.error is not None or "not found" in res.output or "not recognized" in res.output

def test_bash_timeout():
    res = bash(command="python -c \"import time; time.sleep(5)\"", timeout=1)
    assert res.success is False
    assert "timed out" in res.error.lower()

def test_bash_output_truncation():
    # Generate 3000 lines
    cmd = "python -c \"for i in range(3000): print(f'line {i}')\""
    res = bash(command=cmd)
    assert res.success is True
    assert res.output.startswith("[Truncated")
    assert "line 2999" in res.output
