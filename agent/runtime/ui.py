from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from contextlib import contextmanager

console = Console()

def print_banner(model: str, project_dir: str, file_count: int) -> None:
    """Print the stylized startup banner."""
    text = f"[bold cyan]Model:[/bold cyan] {model} | [bold green]Project:[/bold green] {project_dir}\n[bold yellow]Indexed:[/bold yellow] {file_count} files"
    panel = Panel(text, title="[bold magenta]⚡ Forge Agent[/bold magenta]", expand=False, border_style="cyan")
    console.print(panel)

def print_error(msg: str) -> None:
    console.print(f"[bold red]❌ Error:[/bold red] {msg}")

def print_success(msg: str) -> None:
    console.print(f"[bold green]✅ {msg}[/bold green]")

def print_markdown(content: str) -> None:
    console.print(Markdown(content))

def print_diff(diff_content: str) -> None:
    syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=False)
    panel = Panel(syntax, title="[bold blue]📝 Code Modifications[/bold blue]", border_style="blue", expand=False)
    console.print(panel)

@contextmanager
def status_spinner(msg: str):
    """Context manager for showing a loading spinner."""
    with console.status(f"[bold cyan]{msg}...[/bold cyan]", spinner="dots") as status:
        yield status
