import click
from click.testing import CliRunner
from runtime.main import main

def test_root_command_requires_subcommand():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code != 0
    assert "Usage:" in result.output

def test_root_command_accepts_global_options(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ['--project', '.', '--model', 'gemini-2.5-pro', 'chat', '--help'])
    assert result.exit_code == 0
    assert "Start an interactive coding session" in result.output
