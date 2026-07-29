import os
import re
from pathlib import Path
from typing import List, Optional
from runtime.tools.base import ToolResult, tool

@tool(description="Read text file contents with line offset and limit.")
def read_file(path: str, offset: int = 1, limit: int = 2000) -> ToolResult:
    try:
        fpath = Path(path)
        if not fpath.is_file():
            return ToolResult(success=False, output="", error=f"File not found: {path}")

        lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, offset - 1)
        end = start + limit
        selected = lines[start:end]

        formatted = "\n".join(f"{i + start + 1}: {line}" for i, line in enumerate(selected))
        return ToolResult(success=True, output=formatted)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))

@tool(description="Replace exact old_text block with new_text block in target file.")
def edit_file(path: str, old_text: str, new_text: str) -> ToolResult:
    try:
        fpath = Path(path)
        if not fpath.is_file():
            return ToolResult(success=False, output="", error=f"File not found: {path}")

        content = fpath.read_text(encoding="utf-8", errors="replace")
        if old_text not in content:
            return ToolResult(success=False, output="", error=f"Target text not found in {path}")

        updated = content.replace(old_text, new_text, 1)
        fpath.write_text(updated, encoding="utf-8")
        return ToolResult(success=True, output=f"Successfully updated {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))

@tool(description="Create or overwrite file with given content.")
def write_file(path: str, content: str) -> ToolResult:
    try:
        fpath = Path(path)
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
        return ToolResult(success=True, output=f"Successfully wrote {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))

@tool(description="Search for query pattern across text files in directory.")
def search(query: str, path: str = ".") -> ToolResult:
    try:
        root = Path(path)
        if not root.exists():
            return ToolResult(success=False, output="", error=f"Directory not found: {path}")

        matches = []
        pattern = re.compile(query)

        for fpath in root.rglob("*"):
            if fpath.is_file() and not any(part.startswith(".") for part in fpath.parts):
                try:
                    lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines, 1):
                        if pattern.search(line):
                            rel_path = fpath.relative_to(root)
                            matches.append(f"{rel_path}:{idx}: {line.strip()}")
                except Exception:
                    continue

        output = "\n".join(matches) if matches else "No matches found."
        return ToolResult(success=True, output=output)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))

@tool(description="List files and subdirectories in directory.")
def list_dir(path: str = ".") -> ToolResult:
    try:
        root = Path(path)
        if not root.is_dir():
            return ToolResult(success=False, output="", error=f"Not a directory: {path}")

        items = []
        for item in sorted(root.iterdir()):
            if not item.name.startswith("."):
                kind = "[DIR]" if item.is_dir() else "[FILE]"
                items.append(f"{kind} {item.name}")

        return ToolResult(success=True, output="\n".join(items))
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))
