import time
from contextlib import contextmanager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table

console = Console()


def format_context_gauge(used_tokens: int, limit_tokens: int = 128000, width: int = 20) -> str:
    """Format a context window progress gauge with dynamic colors."""
    if limit_tokens <= 0:
        limit_tokens = 128000
    pct = min(1.0, max(0.0, used_tokens / limit_tokens))
    filled = int(round(pct * width))
    bar = "█" * filled + "░" * (width - filled)
    pct_str = f"{pct * 100:.1f}%"
    
    if pct < 0.5:
        color = "bold green"
    elif pct < 0.8:
        color = "bold yellow"
    else:
        color = "bold red"
        
    return f"[{color}][{bar}] {pct_str} ({used_tokens:,} / {limit_tokens:,} tokens)[/{color}]"


class UIManager:
    """Centralized UI Manager for God-Mode styling, telemetry, and cards."""
    
    def __init__(self, console_obj: Console = console):
        self.console = console_obj
        self.total_tokens = 0
        self.start_time = time.time()
        
    def add_tokens(self, count: int) -> None:
        if count > 0:
            self.total_tokens += count
            
    def reset_telemetry(self) -> None:
        self.total_tokens = 0
        self.start_time = time.time()
        
    def get_elapsed_sec(self) -> float:
        return time.time() - self.start_time


ui_manager = UIManager()


def print_banner(model: str, project_dir: str, file_count: int, context_used: int = 0, context_limit: int = 128000) -> None:
    """Print the stylized God-Mode startup ASCII banner."""
    gauge = format_context_gauge(context_used, context_limit, width=15)
    ascii_art = (
        r"[bold cyan] ⚡ ╔═══════════════════════════════════════════════════════════════════════════╗ ⚡[/bold cyan]" "\n"
        r"[bold magenta] ⚡ ║   ___   ____ _____ _   _ _____   _____ ____  ____   ____ _____           ║ ⚡[/bold magenta]" "\n"
        r"[bold magenta] ⚡ ║  / _ \ / ___| ____| \ | |_   _| |  ___/ __ \|  _ \ / ___| ____|          ║ ⚡[/bold magenta]" "\n"
        r"[bold magenta] ⚡ ║ | |_| | |  _|  _| |  \| | | |   | |_ | |  | | |_) | |  _|  _|            ║ ⚡[/bold magenta]" "\n"
        r"[bold magenta] ⚡ ║ |  _  | |_| | |___| |\  | | |   |  _|| |__| |  _ <| |_| | |___           ║ ⚡[/bold magenta]" "\n"
        r"[bold magenta] ⚡ ║ |_| |_|\____|_____|_| \_| |_|   |_|   \____/|_| \_\\____|_____|          ║ ⚡[/bold magenta]" "\n"
        r"[bold cyan] ⚡ ║                                                                           ║ ⚡[/bold cyan]" "\n"
        f"[bold yellow] ⚡ ║  Model: [bold white]{model}[/bold white]  │  Project: [bold white]{project_dir}[/bold white]  │  Files: [bold white]{file_count} indexed[/bold white]          ║ ⚡[/bold yellow]" "\n"
        f" ⚡ ║  Context Window: {gauge}      ║ ⚡" "\n"
        r"[bold cyan] ⚡ ╚═══════════════════════════════════════════════════════════════════════════╝ ⚡[/bold cyan]"
    )
    console.print(ascii_art)


def print_error(msg: str) -> None:
    console.print(f"[bold red]❌ Error:[/bold red] {msg}")


def print_success(msg: str) -> None:
    console.print(f"[bold green]✅ {msg}[/bold green]")


def print_markdown(content: str) -> None:
    console.print(Markdown(content))


def print_diff(diff_content: str) -> None:
    syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=False)
    panel = Panel(syntax, title="[bold cyan]📝 Unified Diff Modifications[/bold cyan]", border_style="cyan", expand=False)
    console.print(panel)


def render_task_header(task_id: int, total_tasks: int, goal: str, target_files: list[str] | None = None) -> None:
    files_str = ", ".join(target_files) if target_files else "Auto-detected"
    text = f"[bold yellow]Goal:[/bold yellow] {goal}\n[bold cyan]Target Files:[/bold cyan] {files_str}"
    panel = Panel(text, title=f"[bold magenta]⚡ [TASK {task_id}/{total_tasks}][/bold magenta]", border_style="magenta", expand=False)
    console.print(panel)


def render_step(step_num: int, total_steps: int, name: str, status: str = "running", detail: str = "") -> None:
    if status == "running":
        badge = "[bold yellow]⏳[/bold yellow]"
    elif status in ("done", "passed"):
        badge = "[bold green]✓[/bold green]"
    elif status == "failed":
        badge = "[bold red]❌[/bold red]"
    else:
        badge = "[bold blue]•[/bold blue]"
        
    detail_str = f" ... [italic]{detail}[/italic]" if detail else ""
    console.print(f"  {badge} [bold cyan]{step_num}/{total_steps}[/bold cyan] [bold white]{name}[/bold white]{detail_str}")


def render_subagent_card(title: str, content: str, border_style: str = "cyan", is_diff: bool = False) -> None:
    if is_diff:
        body = Syntax(content, "diff", theme="monokai", line_numbers=False)
    else:
        body = Markdown(content) if isinstance(content, str) and content.startswith("#") else Text(str(content))
        
    panel = Panel(body, title=f"[bold]{title}[/bold]", border_style=border_style, expand=False)
    console.print(panel)


def render_summary_card(goal: str, completed: list[str], failed: list[str], files_modified: list[str], tokens_used: int = 0, elapsed_sec: float = 0.0) -> None:
    table = Table(title="[bold magenta]📊 God-Mode Session Summary[/bold magenta]", border_style="magenta")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="bold white")
    
    table.add_row("Goal", goal)
    table.add_row("Completed Tasks", str(len(completed)))
    table.add_row("Failed Tasks", str(len(failed)))
    table.add_row("Files Modified", ", ".join(files_modified) if files_modified else "None")
    table.add_row("Tokens Used", f"{tokens_used:,}" if tokens_used else "N/A")
    table.add_row("Elapsed Time", f"{elapsed_sec:.2f}s" if elapsed_sec > 0 else "N/A")
    
    console.print(table)


@contextmanager
def status_spinner(msg: str):
    """Context manager for showing a loading spinner."""
    with console.status(f"[bold cyan]{msg}...[/bold cyan]", spinner="dots") as status:
        yield status
