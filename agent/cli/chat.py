import sys
import click
from runtime.gate import classify_input
from runtime.indexer import generate_project_context

from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, print_resume_banner, save_session_state

@click.command("chat")
@click.pass_context
def chat_cmd(ctx):
    """Start an interactive coding session."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj['model']
    port = ctx.obj['port']
    ctx_size = ctx.obj['ctx_size']
    server_bin = ctx.obj['server_bin']
    
    click.echo(f"🏠 Project: {project_dir}")
    click.echo(f"🤖 Model: {model}")
    
    click.echo("✅ assuming model server is running or reachable.")
        
    print("🔍 Indexing project...")
    
    project_ctx = generate_project_context(project_dir)
    file_count = project_ctx.count("\n") - 5
    print(f"📁 Indexed {file_count} files")

    state = load_session_state(project_dir)
    print_resume_banner(state)

    click.echo("\n💬 Enter your coding request (prefix with '/plan <request>' for multi-step planning, or Ctrl+C to exit):\n")
    
    while True:
        try:
            query = input("you> ").strip()
            if not query: continue
            if query.lower() in ("exit", "quit", "q"): break

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

                if completed: state.completed_tasks.extend(completed)
                elif not failed: state.completed_tasks.append(query)
                if failed: state.open_errors.extend(failed)
                
                for f in files_mod:
                    if f not in state.last_files_modified:
                        state.last_files_modified.append(f)
            else:
                state.completed_tasks.append(query)

            state.pending_tasks = []
            save_session_state(state, project_dir)
            print()
            
        except KeyboardInterrupt:
            click.echo("\n👋 Bye!")
            break
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
