"""Workspace file tree generator."""

import os
import pathlib

IGNORED_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".agent_memory",
    ".superpowers",
    ".agents",
    ".pytest_cache",
    ".vscode",
    "temp_test_db",
}


def generate_filetree(project_path: str, max_files: int = 500) -> str:
    """Generates a formatted markdown string representing the file tree of a project.

    Args:
        project_path: Path to the project root directory.
        max_files: Maximum number of files to include in the list.

    Returns:
        String with header '## File Tree' followed by sorted relative file paths.
    """
    abs_project_path = pathlib.Path(project_path).resolve()
    rel_files: list[str] = []

    for root, dirs, files in os.walk(abs_project_path):
        # Prune ignored directories in-place to avoid descending into them
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = pathlib.Path(root) / file
            try:
                rel_path = file_path.relative_to(abs_project_path).as_posix()
            except ValueError:
                rel_path = os.path.relpath(file_path, abs_project_path).replace("\\", "/")
            rel_files.append(rel_path)

    rel_files.sort()
    if len(rel_files) > max_files:
        rel_files = rel_files[:max_files]

    lines = ["## File Tree"]
    if rel_files:
        lines.extend(rel_files)

    return "\n".join(lines)
