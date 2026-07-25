import click
from click.testing import CliRunner
from cli.config import config_cmd

def test_config_command_help():
    runner = CliRunner()
    result = runner.invoke(config_cmd, ['--help'])
    assert result.exit_code == 0
    assert "Manage workspace configuration" in result.output
