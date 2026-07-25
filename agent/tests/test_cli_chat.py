import click
from click.testing import CliRunner
from cli.chat import chat_cmd

def test_chat_command_help():
    runner = CliRunner()
    result = runner.invoke(chat_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Start an interactive coding session" in result.output
