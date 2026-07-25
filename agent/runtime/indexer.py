"""Project Indexer module.

Scans a project directory and builds a lightweight file index and formatted context.
"""

import os
import pathlib
from typing import Any

INCLUDE_EXTENSIONS = {".py", ".md", ".toml", ".txt", ".yaml", ".yml", ".json", ".cfg"}
EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", ".agent_memory", ".superpowers", ".agents"}


def index_project(project_path: str) -> dict[str, Any]:
    """Scans the project directory and returns a dictionary with 'tree' and 'summaries'.

    Args:
        project_path: Path to the project root directory.

    Returns:
        dict containing:
            - 'tree': sorted list of relative file paths
            - 'summaries': dict mapping relative file path to the first 30 lines of file content
    """
    abs_project_path = pathlib.Path(project_path).resolve()
    tree: list[str] = []
    summaries: dict[str, str] = {}

    for root, dirs, files in os.walk(abs_project_path):
        # Exclude specified directories in-place and sort for determinism
        dirs[:] = sorted([d for d in dirs if d not in EXCLUDE_DIRS])
        files.sort()

        for file in files:
            file_path = pathlib.Path(root) / file
            if file_path.suffix.lower() not in INCLUDE_EXTENSIONS:
                continue

            try:
                rel_path = file_path.relative_to(abs_project_path).as_posix()
            except ValueError:
                rel_path = os.path.relpath(file_path, abs_project_path).replace("\\", "/")

            tree.append(rel_path)

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.read().splitlines()[:30]
                    summaries[rel_path] = "\n".join(lines)
            except OSError:
                # Handle OSError gracefully (skip unreadable files/summaries)
                pass

    tree.sort()
    return {
        "tree": tree,
        "summaries": summaries,
    }


def generate_project_context(project_path: str) -> str:
    """Generates a formatted markdown string representing project context.

    Args:
        project_path: Path to the project root directory.

    Returns:
        Formatted markdown string containing project name, root, file count, and file tree.
    """
    abs_root = pathlib.Path(project_path).resolve()
    project_name = abs_root.name
    index_data = index_project(str(abs_root))

    tree = index_data["tree"]
    file_count = len(tree)

    lines = [
        "# Project Context",
        "",
        f"**Project:** {project_name}",
        f"**Root:** {abs_root}",
        "",
        f"## File Tree ({file_count} files)",
        "",
    ]
    if tree:
        lines.extend(f"  {f}" for f in tree)

    return "\n".join(lines)
