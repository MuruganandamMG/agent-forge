import click
from runtime.session_state import load_session_state
from runtime.ui import console
from rich.panel import Panel
from rich.tree import Tree

@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show current session status and history."""
    project_dir = ctx.obj['project_dir']
    state = load_session_state(project_dir)
    
    tree = Tree(f"[bold magenta]📊 Session Status for {project_dir}[/bold magenta]")
    
    if state.last_goal:
        tree.add(f"[bold cyan]🎯 Last Goal:[/bold cyan] {state.last_goal}")
    else:
        tree.add("[bold cyan]🎯 Last Goal:[/bold cyan] None")
        
    completed_node = tree.add("[bold green]✅ Completed Tasks[/bold green]")
    if state.completed_tasks:
        for task in state.completed_tasks[-5:]:
            completed_node.add(task)
    else:
        completed_node.add("[dim](None)[/dim]")
        
    pending_node = tree.add("[bold yellow]⏳ Pending Tasks[/bold yellow]")
    if state.pending_tasks:
        for task in state.pending_tasks:
            pending_node.add(task)
    else:
        pending_node.add("[dim](None)[/dim]")
        
    error_node = tree.add("[bold red]❌ Open Errors[/bold red]")
    if state.open_errors:
        for err in state.open_errors:
            error_node.add(err)
    else:
        error_node.add("[dim](None)[/dim]")
        
    file_node = tree.add("[bold blue]📝 Recently Modified Files[/bold blue]")
    if state.last_files_modified:
        for f in state.last_files_modified[-5:]:
            file_node.add(f)
    else:
        file_node.add("[dim](None)[/dim]")
        
    console.print(Panel(tree, expand=False, border_style="magenta"))
