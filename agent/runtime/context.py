"""Prompt builder: assembles context within a token budget."""

from runtime.models import count_tokens


def build_context(
    query: str,
    memory,  # Memory instance or duck-typed object with .retrieve()
    file_contents: str,
    style: str,
    token_budget: int = 6000,
) -> str:
    """Build the context string for the executor, trimmed to token budget.

    Priority order (highest to lowest):
    1. Style guide (always included in full)
    2. File contents (trimmed if needed)
    3. Memory results (trimmed if needed)
    """
    sections: list[tuple[str, str]] = []

    # Priority 1: Style (always full)
    if style:
        sections.append(("STYLE", style))

    # Priority 2: File contents
    if file_contents:
        sections.append(("CURRENT FILES", file_contents))

    # Priority 3: Memory
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
