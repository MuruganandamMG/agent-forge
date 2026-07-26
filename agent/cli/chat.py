import sys
import click
from runtime.gate import classify_input
from runtime.indexer import generate_project_context
from runtime.scheduler import run_agent
from runtime.session_state import load_session_state, print_resume_banner, save_session_state
from runtime.chat_responder import generate_chat_response
from runtime.ui import print_banner, print_error, print_markdown, status_spinner, console

@click.command("chat")
@click.pass_context
def chat_cmd(ctx):
    """Start an interactive coding session."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj['model']
    
    with status_spinner("Indexing project"):
        project_ctx = generate_project_context(project_dir)
        file_count = project_ctx.count("\n") - 5
    
    print_banner(model, project_dir, file_count)

    state = load_session_state(project_dir)
    print_resume_banner(state)

    console.print("\n[bold]💬 Enter your coding request[/bold] (prefix with '/plan <request>' for multi-step planning, or Ctrl+C to exit):\n")
    
    while True:
        try:
            query = console.input("[bold cyan]you>[/bold cyan] ").strip()
            if not query: continue
            if query.lower() in ("exit", "quit", "q"): break

            state.append_chat_message("user", query)

            with status_spinner("Thinking"):
                intent = classify_input(query, project_context=project_ctx)
                
            if intent in ("trivial", "vague", "chat"):
                with status_spinner("Generating response"):
                    response = generate_chat_response(query, state.chat_history[:-1], project_ctx)
                console.print(f"\n🤖 [italic]{response}[/italic]\n")
                state.append_chat_message("assistant", response)
                save_session_state(state, project_dir)
                continue

            # It's a task
            with status_spinner("Executing agent task"):
                res = run_agent(query, project_dir, project_context=project_ctx)
                
            state.last_goal = query
            state.append_chat_message("assistant", f"[Executed task: {query}]")
            
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
            console.print("\n")
            
        except KeyboardInterrupt:
            console.print("\n[bold magenta]👋 Bye![/bold magenta]")
            break
        except Exception as e:
            print_error(str(e))
