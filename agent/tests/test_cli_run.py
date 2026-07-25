import click
from click.testing import CliRunner
from cli.run import run_cmd
from unittest.mock import patch

def test_run_command_help():
    runner = CliRunner()
    result = runner.invoke(run_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Execute a single task" in result.output
