import click
from runtime.session_state import load_session_state
from runtime.ui import console, format_context_gauge
from rich.panel import Panel
from rich.tree import Tree

@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show current session status and history."""
    project_dir = ctx.obj['project_dir']
    model = ctx.obj.get('model', 'gemini-2.5-pro')
    state = load_session_state(project_dir)
    
    tree = Tree(f"[bold magenta]⚡ God-Mode Session Status: [white]{project_dir}[/white][/bold magenta]")
    
    tree.add(f"[bold cyan]🤖 Model:[/bold cyan] {model}")
    tree.add(f"[bold yellow]⚡ Context Window:[/bold yellow] {format_context_gauge(used_tokens=22000, limit_tokens=128000, width=15)}")
    
    if state.last_goal:
        tree.add(f"[bold cyan]🎯 Last Goal:[/bold cyan] {state.last_goal}")
    else:
        tree.add("[bold cyan]🎯 Last Goal:[/bold cyan] None")
        
    completed_node = tree.add("[bold green]✅ Completed Tasks[/bold green]")
    if state.completed_tasks:
        for task in state.completed_tasks[-5:]:
            completed_node.add(f"[green]{task}[/green]")
    else:
        completed_node.add("[dim](None)[/dim]")
        
    pending_node = tree.add("[bold yellow]⏳ Pending Tasks[/bold yellow]")
    if state.pending_tasks:
        for task in state.pending_tasks:
            pending_node.add(f"[yellow]{task}[/yellow]")
    else:
        pending_node.add("[dim](None)[/dim]")
        
    error_node = tree.add("[bold red]❌ Open Errors[/bold red]")
    if state.open_errors:
        for err in state.open_errors:
            error_node.add(f"[red]{err}[/red]")
    else:
        error_node.add("[dim](None)[/dim]")
        
    file_node = tree.add("[bold blue]📝 Recently Modified Files[/bold blue]")
    if state.last_files_modified:
        for f in state.last_files_modified[-5:]:
            file_node.add(f"[blue]{f}[/blue]")
    else:
        file_node.add("[dim](None)[/dim]")
        
    console.print(Panel(tree, expand=False, border_style="magenta"))
