from runtime.models import chat

SYSTEM_PROMPT = """You are the Forge Coding Agent, a capable CLI-based AI assistant.
The user just sent a conversational or vague message (not an explicit coding task).
Respond politely, conversationally, and concisely.
If they ask what you can do, explain you can build, refactor, and fix code in their project.
Keep responses under 3 sentences unless explaining a complex topic.

Project Context Summary:
{project_context}
"""

def generate_chat_response(query: str, history: list[dict[str, str]], project_context: str) -> str:
    """Generate a lightweight conversational response using chat history."""
    # Truncate project context heavily to save tokens on chat
    truncated_ctx = project_context[:1000] + ("..." if len(project_context) > 1000 else "")
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(project_context=truncated_ctx)}
    ]
    
    # Append history
    for msg in history:
        if msg.get("content", "").strip():  # Skip empty messages
            messages.append(msg)
        
    # Append current query
    messages.append({"role": "user", "content": query})
    
    try:
        # Use low max_tokens for chat responses
        res = chat(messages, temperature=0.7, max_tokens=500).strip()
        if not res:
            return "🙂 Tell me what you'd like me to build, fix, or change."
        return res
    except Exception as e:
        return f"🙂 Tell me what you'd like me to build, fix, or change. (API Error: {str(e)})"
