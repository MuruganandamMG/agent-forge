import pytest
from cli.tui import handle_slash_command

def test_handle_slash_command_help():
    handled, output = handle_slash_command("/help")
    assert handled is True
    assert "/plan" in output
    assert "/status" in output

def test_handle_slash_command_clear():
    handled, output = handle_slash_command("/clear")
    assert handled is True
    assert "cleared" in output.lower()

def test_handle_slash_command_unknown():
    handled, output = handle_slash_command("/nonexistent")
    assert handled is True
    assert "unknown" in output.lower()

def test_non_slash_command():
    handled, output = handle_slash_command("Hello agent")
    assert handled is False
    assert output == ""
