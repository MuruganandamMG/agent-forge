"""Simple task list representing the planner's output."""

import json
import re


class TaskGraph:
    """Ordered list of tasks parsed from planner JSON output."""

    def __init__(self, goal: str, tasks: list[dict]) -> None:
        self.goal = goal
        self.tasks = tasks

    @classmethod
    def from_plan_json(cls, json_str: str) -> "TaskGraph":
        """Parse planner output JSON into a TaskGraph."""
        cleaned = json_str.strip()

        # Extract content inside markdown fences if present
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
            else:
                lines = cleaned.split("\n")
                lines = [line for line in lines if not line.strip().startswith("```")]
                cleaned = "\n".join(lines).strip()

        # Try direct JSON parsing
        data = None
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: find outer-most curly braces
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extracted = cleaned[first_brace : last_brace + 1]
                try:
                    data = json.loads(extracted)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse plan JSON: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Planner output is not a valid JSON object")

        goal = data.get("goal", "")
        tasks = data.get("tasks", [])
        for task in tasks:
            task.setdefault("type", "code")
            task.setdefault("status", "pending")
            task.setdefault("failure_reason", "")
        return cls(goal=goal, tasks=tasks)

    def next_task(self) -> dict | None:
        """Return the next pending task, or None if all are done/failed."""
        for task in self.tasks:
            if task["status"] == "pending":
                return task
        return None

    def mark_done(self, task_id: int) -> None:
        """Mark a task as completed."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "done"
                return
        raise KeyError(f"Task {task_id} not found")

    def mark_failed(self, task_id: int, reason: str) -> None:
        """Mark a task as failed with a reason."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "failed"
                task["failure_reason"] = reason
                return
        raise KeyError(f"Task {task_id} not found")

    def summary(self) -> str:
        """Return a human-readable summary of task statuses."""
        lines = [f"Goal: {self.goal}", ""]
        for t in self.tasks:
            icon = {"done": "✅", "failed": "❌", "pending": "⬜"}.get(t["status"], "?")
            lines.append(f"  {icon} Task {t['id']}: {t['description']}")
            if t.get("failure_reason"):
                lines.append(f"     Reason: {t['failure_reason']}")
        return "\n".join(lines)
