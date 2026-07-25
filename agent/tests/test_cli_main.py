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
    model_path = tmp_path / "model.gguf"
    model_path.write_text("")
    result = runner.invoke(main, ['--project', '.', '--model', str(model_path), 'chat', '--help'])
    assert result.exit_code == 0
    assert "Start an interactive coding session" in result.output
