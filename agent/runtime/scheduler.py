"""Main orchestration loop: planner -> executor -> validate -> apply -> report."""

from pathlib import Path

from runtime.context import build_context
from runtime.enricher import enrich_request
from runtime.memory import Memory
from runtime.models import chat
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


def _plan(user_query: str, context: str = "") -> str:
    """Call the planner role to generate a JSON task plan."""
    system = _load_prompt("planner_system.txt")
    messages: list[dict] = [
        {"role": "system", "content": system},
    ]
    if context:
        messages.append({"role": "user", "content": f"CONTEXT:\n{context}"})
    messages.append({"role": "user", "content": user_query})

    return chat(messages, temperature=0.2)


def _execute(task: dict, file_contents: str, style: str, context: str = "") -> str:
    """Call the executor role to generate a unified diff for one task."""
    system = _load_prompt("executor_system.txt")
    user_content = f"TASK:\n{task['description']}\n\nFILES:\n{task.get('files', [])}"
    if file_contents:
        user_content += f"\n\nCURRENT FILE CONTENTS:\n{file_contents}"
    if style:
        user_content += f"\n\nSTYLE:\n{style}"
    if context:
        user_content += f"\n\nADDITIONAL CONTEXT:\n{context}"

    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    stop_seqs = ["```\n\n", "\n\nTask:", "<|im_end|>"]
    return chat(messages, temperature=0.1, max_tokens=800, stop=stop_seqs)


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
        print("🧠 Planning...")
        plan_json = _plan(enriched_query, context=project_context)
        try:
            task_graph = TaskGraph.from_plan_json(plan_json)
        except ValueError:
            print(f"\n🤖 {plan_json.strip()}\n")
            return AgentResult(
                goal=clean_query,
                completed=[],
                failed=[plan_json],
                files_modified=[],
                summary=plan_json,
                raw=plan_json,
            )

        print(f"📋 Plan: {task_graph.goal}")
        print(task_graph.summary())
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

        print(f"\n⚡ Executing Task {task_id}: {task['description']}")

        file_contents = _gather_file_contents(task.get("files", []), project_dir)
        extra_context = build_context(
            query=task["description"],
            memory=memory,
            file_contents="",
            style="",
            token_budget=2000,
        )
        if project_context:
            extra_context = f"{project_context}\n\n{extra_context}".strip()
        last_error = ""

        for attempt in range(1, MAX_RETRIES + 1):
            # Generate diff
            if last_error:
                task_with_error = dict(task)
                task_with_error["description"] += (
                    f"\n\n--- PREVIOUS ATTEMPT FAILED ---\n"
                    f"Attempt: {attempt - 1}/{MAX_RETRIES}\n"
                    f"Error:\n{last_error}\n"
                    f"--- END ERROR ---\n"
                    f"Fix the issues above and generate a corrected diff."
                )
                diff = _execute(task_with_error, file_contents, style, context=extra_context)
            else:
                diff = _execute(task, file_contents, style, context=extra_context)

            # Try to apply the diff
            if not diff.strip():
                last_error = "Executor returned empty output."
                print(f"  ⚠️ Attempt {attempt}: empty diff")
                continue

            applied = sandbox.apply_diff(diff)
            if not applied:
                last_error = "git apply failed on the generated diff."
                print(f"  ⚠️ Attempt {attempt}: diff didn't apply cleanly")
                continue

            # Validate
            vresult = validate(project_dir, run_pytest=True)
            if vresult.passed:
                # Ask for human approval
                print(f"\n  ✅ Validation passed. Diff for Task {task_id}:")
                print("  " + "-" * 60)
                print(diff)
                print("  " + "-" * 60)
                approval = input("  Apply this change? [y/n]: ").strip().lower()
                if approval == "y":
                    commit_hash = sandbox.checkpoint(task["description"])
                    task_graph.mark_done(task_id)
                    completed.append(task["description"])
                    for f in task.get("files", []):
                        if f not in files_modified:
                            files_modified.append(f)
                    print(f"  ✅ Applied and committed: {commit_hash[:8]}")

                    if memory is not None:
                        try:
                            memory.store_session(
                                user_query, f"Task {task_id}: {task['description']}"
                            )
                            memory.reflect(
                                task["description"],
                                f"Applied diff to {task.get('files', [])}",
                            )
                        except Exception:
                            pass
                else:
                    sandbox._run_git("checkout", ".", check=False)
                    task_graph.mark_failed(task_id, "User rejected")
                    failed.append(f"Task {task_id} ({task['description']}): User rejected")
                    print("  ⏭️ Skipped by user")
                break
            else:
                last_error = f"[{vresult.stage}] {vresult.errors[:500]}"
                print(f"  ⚠️ Attempt {attempt}: validation failed at {vresult.stage}")
                # Revert the failed application
                sandbox._run_git("checkout", ".")
        else:
            task_graph.mark_failed(
                task_id, f"Max retries ({MAX_RETRIES}) exceeded: {last_error}"
            )
            failed.append(f"Task {task_id} ({task['description']}): {last_error}")
            print(f"  ❌ Task {task_id} failed after {MAX_RETRIES} attempts")

    # Summary
    summary = task_graph.summary()
    print(f"\n{'=' * 60}")
    print("📊 Session Summary")
    print(summary)
    return AgentResult(
        goal=task_graph.goal,
        completed=completed,
        failed=failed,
        files_modified=files_modified,
        summary=summary,
    )


