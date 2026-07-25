"""Request enrichment module for pre-processing raw user queries with file context."""

from runtime.models import chat

ENRICHER_SYSTEM_PROMPT = """You are a request enricher for a coding assistant.
Given a user's coding request and the project file tree,
identify which files are likely relevant, what related files might be affected,
and any useful context. Be concise.

Format your response as:
Files: <comma-separated list of relevant files>
Related: <comma-separated list of related files>
Context: <one sentence of useful context>"""


def enrich_request(raw_query: str, project_context: str, memory_context: str = "") -> str:
    """Enrich a user request with project file context and session context via LLM."""
    user_parts = [
        f"Request: {raw_query}",
        f"Project files: {project_context}",
    ]
    if memory_context:
        user_parts.append(f"Recent session context: {memory_context}")

    user_content = "\n\n".join(user_parts)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": ENRICHER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        enrichment_text = chat(
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
            stop=["<|im_end|>"],
        )
        return f"{raw_query}\n\n--- Enrichment ---\n{enrichment_text}"
    except Exception:
        return raw_query
