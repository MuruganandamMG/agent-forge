"""CLI entry point for the local coding agent."""

import sys
from pathlib import Path

if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

import click

from runtime.gate import classify_input
from runtime.indexer import generate_project_context
from runtime.models import ensure_server, health_check
from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, print_resume_banner, save_session_state

DEFAULT_MODEL = r"E:\AI\Models\Agentic AI's in CLI\Qwen3-8B\Qwen3-8B-Q4_K_M.gguf"

@click.group(invoke_without_command=False)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Path to the project directory to work on.",
)
@click.option(
    "--model",
    "-m",
    type=click.Path(exists=True),
    default=DEFAULT_MODEL,
    help="Path to the GGUF model file.",
)
@click.option("--port", default=8081, help="Port for llama-server.")
@click.option("--ctx-size", "-c", default=8192, help="Context size for llama-server.")
@click.option("--server-bin", default=None, help="Path to llama-server binary.")
@click.pass_context
def main(ctx: click.Context, project: str, model: str, port: int, ctx_size: int, server_bin: str | None) -> None:
    """Local Coding Agent — autonomous coding assistant."""
    ctx.ensure_object(dict)
    project_dir = str(Path(project).resolve())
    ctx.obj['project_dir'] = project_dir
    ctx.obj['model'] = model
    ctx.obj['port'] = port
    ctx.obj['ctx_size'] = ctx_size
    ctx.obj['server_bin'] = server_bin

from cli.chat import chat_cmd
from cli.run import run_cmd
main.add_command(chat_cmd)
main.add_command(run_cmd)

if __name__ == "__main__":
    main.add_command(chat_cmd)
    main()
