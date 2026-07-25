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


@click.command()
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
def main(project: str, model: str, port: int, ctx_size: int, server_bin: str | None) -> None:
    """Local Coding Agent — autonomous coding assistant."""
    project_dir = str(Path(project).resolve())
    click.echo(f"🏠 Project: {project_dir}")
    click.echo(f"🤖 Model: {model}")

    # Ensure model server is running
    if not health_check():
        click.echo("🚀 Starting llama-server...")
        try:
            proc = ensure_server(model, port=port, ctx_size=ctx_size, server_bin=server_bin)
            if proc:
                click.echo(f"✅ llama-server started (PID {proc.pid})")
        except (FileNotFoundError, RuntimeError) as e:
            click.echo(f"❌ {e}", err=True)
            sys.exit(1)
    else:
        click.echo("✅ llama-server already running")

    print("🔍 Indexing project...")
    project_ctx = generate_project_context(project_dir)
    file_count = project_ctx.count("\n") - 5  # rough estimate of file entries
    print(f"📁 Indexed {file_count} files")

    state = load_session_state(project_dir)
    print_resume_banner(state)

    # REPL loop
    click.echo(
        "\n💬 Enter your coding request (prefix with '/plan <request>' for multi-step planning, or Ctrl+C to exit):\n"
    )
    while True:
        try:
            query = input("you> ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                break

            intent = classify_input(query, project_context=project_ctx)
            if intent == "trivial":
                click.echo("🙂 Tell me what you'd like me to build, fix, or change.\n")
                continue
            if intent == "vague":
                click.echo("❓ Can you give me more detail — which file, what behavior?\n")
                continue
            if intent == "chat":
                click.echo("💬 Let's focus on your coding project! What would you like to build or fix?\n")
                continue

            res = run_agent(query, project_dir, project_context=project_ctx)
            state.last_goal = query
            if isinstance(res, dict):
                completed = res.get("completed", [])
                failed = res.get("failed", [])
                files_mod = res.get("files_modified", [])

                if completed:
                    state.completed_tasks.extend(completed)
                elif not failed:
                    state.completed_tasks.append(query)

                if failed:
                    state.open_errors.extend(failed)

                for f in files_mod:
                    if f not in state.last_files_modified:
                        state.last_files_modified.append(f)
            else:
                state.completed_tasks.append(query)

            state.pending_tasks = []  # cleared after execution
            save_session_state(state, project_dir)
            print()
        except KeyboardInterrupt:
            click.echo("\n👋 Bye!")
            break
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)


if __name__ == "__main__":
    main()
