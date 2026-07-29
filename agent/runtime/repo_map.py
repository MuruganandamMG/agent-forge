import ast
from pathlib import Path
from typing import List

def _parse_python_symbols(file_path: Path) -> List[str]:
    symbols = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append(f"  class {node.name}")
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.FunctionDef):
                        args = [a.arg for a in child.args.args]
                        symbols.append(f"    def {child.name}({', '.join(args)})")
            elif isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                symbols.append(f"  def {node.name}({', '.join(args)})")
    except Exception:
        # Fallback regex if AST fails
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("class ") or stripped.startswith("def "):
                    symbols.append(f"  {stripped.split(':')[0]}")
        except Exception:
            pass

    return symbols

def generate_repo_map(project_dir: str) -> str:
    root = Path(project_dir)
    if not root.exists():
        return "Repository directory not found."

    output_lines = ["# Repository Symbol Map\n"]

    for fpath in sorted(root.rglob("*.py")):
        if any(part.startswith(".") or part in ("venv", "node_modules", "build", "dist") for part in fpath.parts):
            continue

        rel_path = fpath.relative_to(root)
        symbols = _parse_python_symbols(fpath)

        if symbols:
            output_lines.append(f"📄 {rel_path}")
            output_lines.extend(symbols)
            output_lines.append("")

    return "\n".join(output_lines).strip()
