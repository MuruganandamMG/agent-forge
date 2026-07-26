"""Main orchestration loop: planner -> executor -> validate -> apply -> report."""

from pathlib import Path

from runtime.context import build_context, load_agents_md
from runtime.enricher import enrich_request
from runtime.filetree import generate_filetree
from runtime.memory import Memory
from runtime.subagents.core import run_implementer, run_planner, run_reviewer
from runtime.sandbox import Sandbox
from runtime.task_graph import TaskGraph
from runtime.validate import validate

MAX_RETRIES = 3

_prompts_dir = Path(__file__).parent.parent / "prompts"
_style_path = Path(__file__).parent.parent / "style.md"


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (_prompts_dir / filename).read_text(encoding="utf-8")


def _load_style() -> str:
    """Load style.md if it exists, else return empty string."""
    if _style_path.exists():
        return _style_path.read_text(encoding="utf-8")
    return ""


def _gather_file_contents(files: list[str], project_dir: str) -> str:
    """Read the contents of relevant files for the executor context."""
    parts = []
    for fpath in files:
        full = Path(project_dir) / fpath
        if full.is_file():
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
                parts.append(f"--- {fpath} ---\n{content}\n")
            except OSError:
                parts.append(f"--- {fpath} --- (could not read)\n")
        else:
            parts.append(f"--- {fpath} --- (new file)\n")
    return "\n".join(parts)


class AgentResult(dict):
    """Structured execution result dictionary, backward compatible with string checks."""

    def __init__(
        self,
        goal: str = "",
        completed: list[str] | None = None,
        failed: list[str] | None = None,
        files_modified: list[str] | None = None,
        summary: str = "",
        raw: str = "",
    ):
        completed_list = completed or []
        failed_list = failed or []
        files_list = files_modified or []
        super().__init__(
            goal=goal,
            completed=completed_list,
            failed=failed_list,
            files_modified=files_list,
            summary=summary,
        )
        self.raw = raw or summary

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.get("summary", "") == other or self.raw == other
        return super().__eq__(other)

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            if item in self.get("summary", "") or item in self.raw:
                return True
        return super().__contains__(item)

    def lower(self) -> str:
        return self.get("summary", "").lower()


def run_agent(user_query: str, project_dir: str, project_context: str = "") -> dict:
    """Full agent loop: plan -> execute each task -> validate -> apply."""
    sandbox = Sandbox(project_dir)
    sandbox.init_git()
    style = _load_style()
    memory_dir = str(Path(project_dir) / ".agent_memory")
    try:
        memory = Memory(memory_dir)
    except Exception:
        memory = None

    # Check if user explicitly requested plan mode via /plan command
    is_plan_mode = user_query.strip().startswith("/plan")
    clean_query = user_query.strip()[5:].strip() if is_plan_mode else user_query.strip()

    enriched_query = enrich_request(clean_query, project_context=project_context, memory_context="")

    if is_plan_mode:
        # Step 1: Multi-step Planner
        from runtime.ui import console
        console.print("[bold cyan]🧠 Planning...[/bold cyan]")
        plan_json = run_planner(enriched_query, project_context=project_context)
        try:
            task_graph = TaskGraph.from_plan_json(plan_json)
        except ValueError:
            console.print(f"\n[italic]{plan_json.strip()}[/italic]\n")
            return AgentResult(
                goal=clean_query,
                completed=[],
                failed=[plan_json],
                files_modified=[],
                summary=plan_json,
                raw=plan_json,
            )

        console.print(f"[bold green]📋 Plan:[/bold green] {task_graph.goal}")
        console.print(task_graph.summary())
    else:
        # Direct execution mode (single task, no planner overhead)
        task_graph = TaskGraph(
            goal=clean_query,
            tasks=[{
                "id": 1,
                "type": "code",
                "description": enriched_query,
                "files": [],
                "status": "pending",
                "failure_reason": "",
            }],
        )

    completed: list[str] = []
    failed: list[str] = []
    files_modified: list[str] = []

    # Step 2: Execute each task
    agents_md = load_agents_md(project_dir)
    file_tree = generate_filetree(project_dir)

    while True:
        task = task_graph.next_task()
        if task is None:
            break

        task_id = task["id"]
        task_type = task.get("type", "code")

        # Handle clarification tasks without hitting the diff/executor/validator pipeline
        if task_type == "clarify" or task.get("description", "").startswith("CLARIFY:"):
            print(f"\n❓ Clarification Needed (Task {task_id}): {task['description']}")
            user_response = input("  Your answer: ").strip()
            task_graph.mark_done(task_id)
            completed.append(task["description"])
            if memory is not None:
                try:
                    memory.store_session(
                        user_query, f"Clarification for Task {task_id}: {user_response}"
                    )
                except Exception:
                    pass
            continue

        from runtime.ui import console, print_error
        console.print(f"\n[bold magenta]⚡ Executing Task {task_id}:[/bold magenta] {task['description']}")

        file_contents = _gather_file_contents(task.get("files", []), project_dir)
        extra_context = build_context(
            query=task["description"],
            memory=memory,
            file_contents="",
            style="",
            agents_md=agents_md,
            file_tree=file_tree,
            token_budget=6000,
        )
        if project_context:
            extra_context = f"{project_context}\n\n{extra_context}".strip()
            
        last_error = ""

        for attempt in range(1, MAX_RETRIES + 1):
            # Generate diff
            diff = run_implementer(task["description"], file_contents, feedback=last_error)

            # Try to apply the diff
            if not diff.strip():
                last_error = "Executor returned empty output."
                console.print(f"  [yellow]⚠️ Attempt {attempt}: empty diff[/yellow]")
                continue

            applied = sandbox.apply_diff(diff)
            if not applied:
                last_error = "git apply failed on the generated diff. Make sure to return standard unified diff format."
                console.print(f"  [yellow]⚠️ Attempt {attempt}: diff didn't apply cleanly[/yellow]")
                continue

            # Validate locally before Subagent Review
            vresult = validate(project_dir, run_pytest=True)
            if not vresult.passed:
                last_error = f"Validation failed at {vresult.stage}: {vresult.errors[:500]}"
                console.print(f"  [yellow]⚠️ Attempt {attempt}: {last_error}[/yellow]")
                sandbox._run_git("checkout", ".")
                continue
                
            # Delegate to Reviewer Subagent
            console.print("  [cyan]🔍 Sending to Reviewer Subagent...[/cyan]")
            review = run_reviewer(task["description"], diff)
            
            if review == "APPROVED":
                commit_hash = sandbox.checkpoint(task["description"])
                task_graph.mark_done(task_id)
                completed.append(task["description"])
                for f in task.get("files", []):
                    if f not in files_modified:
                        files_modified.append(f)
                console.print(f"  [bold green]✅ Approved and committed:[/bold green] {commit_hash[:8]}")

                if memory is not None:
                    try:
                        memory.store_session(user_query, f"Task {task_id}: {task['description']}")
                        memory.reflect(task["description"], f"Applied diff to {task.get('files', [])}")
                    except Exception:
                        pass
                break
            else:
                last_error = f"Reviewer Feedback:\n{review}"
                console.print(f"  [yellow]⚠️ Attempt {attempt}: Reviewer requested changes.[/yellow]")
                sandbox._run_git("checkout", ".")
                
        else:
            task_graph.mark_failed(
                task_id, f"Max retries ({MAX_RETRIES}) exceeded: {last_error}"
            )
            failed.append(f"Task {task_id} ({task['description']}): {last_error}")
            console.print(f"  [bold red]❌ Task {task_id} failed after {MAX_RETRIES} attempts[/bold red]")

    # Summary
    summary = task_graph.summary()
    console.print(f"\n[dim]{'=' * 60}[/dim]")
    console.print("[bold]📊 Session Summary[/bold]")
    console.print(summary)
    return AgentResult(
        goal=task_graph.goal,
        completed=completed,
        failed=failed,
        files_modified=files_modified,
        summary=summary,
    )


