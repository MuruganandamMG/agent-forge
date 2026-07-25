import click
from click.testing import CliRunner
from cli.status import status_cmd

def test_status_command_help():
    runner = CliRunner()
    result = runner.invoke(status_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Show current session status" in result.output
