import click
import os
import sys
from runtime.gate import classify_input
from runtime.indexer import generate_project_context

from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, save_session_state

@click.command("run")
@click.argument("task_input", nargs=-1, required=True)
@click.pass_context
def run_cmd(ctx, task_input):
    """Execute a single task from text or a file and exit."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj['model']
    port = ctx.obj['port']
    ctx_size = ctx.obj['ctx_size']
    server_bin = ctx.obj['server_bin']
    
    input_str = " ".join(task_input).strip()
    file_path = os.path.join(project_dir, input_str)
    
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            query = f.read().strip()
            click.echo(f"📄 Loaded task from {input_str}")
    else:
        query = input_str
        
    if not query:
        raise click.ClickException("Task input cannot be empty.")

    click.echo(f"🏠 Project: {project_dir}")
    click.echo(f"🤖 Model: {model}")
    
    click.echo("✅ assuming model server is running or reachable.")
        
    print("🔍 Indexing project...")
    
    project_ctx = generate_project_context(project_dir)
    state = load_session_state(project_dir)
    
    try:
        intent = classify_input(query, project_context=project_ctx)
        if intent in ("trivial", "vague", "chat"):
            raise click.ClickException(f"Input classified as '{intent}'. Please provide a clear coding task.")
            
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
        click.echo("✅ Task complete.")
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e))
