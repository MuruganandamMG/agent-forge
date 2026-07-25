import click
from runtime.session_state import load_session_state

@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show current session status and history."""
    project_dir = ctx.obj['project_dir']
    state = load_session_state(project_dir)
    
    click.echo(f"📊 Session Status for {project_dir}")
    click.echo("-" * 40)
    
    if state.last_goal:
        click.echo(f"🎯 Last Goal: {state.last_goal}")
    else:
        click.echo("🎯 Last Goal: None")
        
    click.echo("\n✅ Completed Tasks:")
    if state.completed_tasks:
        for task in state.completed_tasks[-5:]: # show last 5
            click.echo(f"  - {task}")
    else:
        click.echo("  (None)")
        
    click.echo("\n⏳ Pending Tasks:")
    if state.pending_tasks:
        for task in state.pending_tasks:
            click.echo(f"  - {task}")
    else:
        click.echo("  (None)")
        
    click.echo("\n❌ Open Errors:")
    if state.open_errors:
        for err in state.open_errors:
            click.echo(f"  - {err}", err=True)
    else:
        click.echo("  (None)")
        
    click.echo("\n📝 Recently Modified Files:")
    if state.last_files_modified:
        for f in state.last_files_modified[-5:]:
            click.echo(f"  - {f}")
    else:
        click.echo("  (None)")
