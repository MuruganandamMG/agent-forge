"""Session state management and persistence for the local coding agent."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass
class SessionState:
    """Persistent state tracking user queries, tasks, modified files, and open errors."""

    last_run: str = ""  # ISO 8601 timestamp
    last_goal: str = ""  # last user query goal
    completed_tasks: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)
    last_files_modified: list[str] = field(default_factory=list)
    open_errors: list[str] = field(default_factory=list)
    chat_history: list[dict[str, str]] = field(default_factory=list)

    def append_chat_message(self, role: str, content: str) -> None:
        """Append a message and trim history to the last 10 messages."""
        self.chat_history.append({"role": role, "content": content})
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

def load_session_state(project_dir: str) -> SessionState:
    """Read session_state.json from project_dir. Returns empty SessionState if missing or corrupt."""
    filepath = Path(project_dir) / "session_state.json"
    if not filepath.exists():
        return SessionState()
    try:
        content = filepath.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict):
            return SessionState()
        return SessionState(
            last_run=str(data.get("last_run") or ""),
            last_goal=str(data.get("last_goal") or ""),
            completed_tasks=list(data.get("completed_tasks") or []),
            pending_tasks=list(data.get("pending_tasks") or []),
            last_files_modified=list(data.get("last_files_modified") or []),
            open_errors=list(data.get("open_errors") or []),
            chat_history=list(data.get("chat_history") or []),
        )
    except Exception:
        return SessionState()


def save_session_state(state: SessionState, project_dir: str) -> None:
    """Save SessionState to session_state.json in project_dir after setting last_run timestamp."""
    state.last_run = datetime.now(timezone.utc).isoformat()
    filepath = Path(project_dir) / "session_state.json"
    data = asdict(state)
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")


def print_resume_banner(state: SessionState) -> None:
    """Print resume banner if last_goal is non-empty, showing tasks and errors."""
    if not state.last_goal:
        return

    print(f"📋 Last session: {state.last_goal}")
    for task in state.completed_tasks[-3:]:
        print(f"   ✅ {task}")
    for task in state.pending_tasks[:3]:
        print(f"   ⏳ {task}")
    for error in state.open_errors[:2]:
        print(f"   ❌ {error}")
