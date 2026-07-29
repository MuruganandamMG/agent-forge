from pathlib import Path

from runtime.models import count_tokens
from runtime.repo_map import generate_repo_map


def load_agents_md(project_dir: str) -> str:
    """Check for AGENTS.md in project_dir or agent/AGENTS.md."""
    p_path = Path(project_dir)
    candidates = [
        p_path / "AGENTS.md",
        p_path / "agent" / "AGENTS.md",
        Path(__file__).parent.parent / "AGENTS.md",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                content = candidate.read_text(encoding="utf-8")
                if content.strip():
                    return content
            except OSError:
                continue
    return ""


def build_context(
    query: str,
    memory=None,  # Memory instance or duck-typed object with .retrieve()
    file_contents: str = "",
    style: str = "",
    agents_md: str = "",
    file_tree: str = "",
    project_dir: str = "",
    token_budget: int = 6000,
) -> str:
    """Build the context string for the executor, trimmed to token budget.

    Priority order (highest to lowest):
    1. AGENTS.md project rules (always included first)
    2. File tree (workspace directory structure)
    3. Repo Symbol Map (class/function skeleton)
    4. Style guide (if provided)
    5. File contents (trimmed if needed)
    6. Memory results (trimmed if needed)
    """
    sections: list[tuple[str, str]] = []

    # Priority 1: AGENTS.md
    if agents_md:
        sections.append(("AGENTS.MD", agents_md))

    # Priority 2: File tree
    if file_tree:
        sections.append(("FILE TREE", file_tree))

    # Priority 3: Repo Symbol Map
    if project_dir:
        repo_map_text = generate_repo_map(project_dir)
        if repo_map_text:
            sections.append(("REPOSITORY SYMBOL MAP", repo_map_text))

    # Priority 4: Style
    if style:
        sections.append(("STYLE", style))

    # Priority 4: File contents
    if file_contents:
        sections.append(("CURRENT FILES", file_contents))

    # Priority 5: Memory
    if memory is not None:
        try:
            memory_results = memory.retrieve(query, collection="reflections", n_results=5)
            memory_results += memory.retrieve(query, collection="sessions", n_results=3)
        except Exception:
            memory_results = []

        if memory_results:
            memory_text = "\n\n".join(r["document"] for r in memory_results)
            sections.append(("RELEVANT MEMORY", memory_text))

    # Assemble and trim
    result_parts = []
    used_tokens = 0

    for label, content in sections:
        section_text = f"\n--- {label} ---\n{content}\n"
        section_tokens = count_tokens(section_text)

        if used_tokens + section_tokens > token_budget:
            # Trim this section to fit
            remaining_tokens = token_budget - used_tokens
            if remaining_tokens > 100:  # worth including a truncated version
                char_limit = remaining_tokens * 4  # rough heuristic
                truncated = content[:char_limit] + "\n... (truncated to fit token budget)"
                section_text = f"\n--- {label} ---\n{truncated}\n"
                result_parts.append(section_text)
            break
        else:
            result_parts.append(section_text)
            used_tokens += section_tokens

    return "".join(result_parts)

