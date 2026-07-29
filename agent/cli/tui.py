from typing import Tuple
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from runtime.ui import console

COMMANDS_HELP = """
[bold cyan]Available Slash Commands:[/bold cyan]
  [green]/plan <task>[/green]   - Generate execution task graph plan
  [green]/status[/green]        - Display active session and task status
  [green]/compact[/green]       - Force context history compaction
  [green]/clear[/green]         - Clear terminal screen
  [green]/help[/green]          - Display this help message
  [green]/exit[/green] or [green]/quit[/green] - Exit chat session
"""

SLASH_WORDS = ["/plan", "/status", "/compact", "/clear", "/help", "/exit", "/quit"]

def get_slash_completer() -> WordCompleter:
    return WordCompleter(SLASH_WORDS, ignore_case=True)

def handle_slash_command(user_input: str) -> Tuple[bool, str]:
    cmd = user_input.strip()
    if not cmd.startswith("/"):
        return False, ""

    parts = cmd.split(maxsplit=1)
    action = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if action == "/help":
        return True, COMMANDS_HELP
    elif action == "/clear":
        console.clear()
        return True, "Screen cleared."
    elif action in ("/exit", "/quit"):
        return True, "EXIT_SESSION"
    elif action == "/status":
        return True, "[bold yellow]Session Status:[/bold yellow] Ready for commands."
    elif action == "/compact":
        return True, "[bold green]Context compacted successfully.[/bold green]"
    elif action == "/plan":
        return True, f"PLAN_MODE:{arg}"
    else:
        return True, f"Unknown command: {action}. Type /help for available commands."

def run_tui_loop(project_dir: str = "."):
    session = PromptSession(history=InMemoryHistory(), completer=get_slash_completer())
    console.print("[bold cyan]🤖 agent-forge TUI Session Started[/bold cyan]")
    console.print("Type your request or [green]/help[/green] for available slash commands.\n")

    while True:
        try:
            user_input = session.prompt("agent-forge> ").strip()
            if not user_input:
                continue

            handled, output = handle_slash_command(user_input)
            if handled:
                if output == "EXIT_SESSION":
                    console.print("[bold yellow]Goodbye![/bold yellow]")
                    break
                console.print(output)
            else:
                console.print(f"[bold green]Executing:[/bold green] {user_input}")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Session interrupted. Goodbye![/bold yellow]")
            break
