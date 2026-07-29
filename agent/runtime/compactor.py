from typing import Any, Dict, List

def estimate_tokens(text: str) -> int:
    return len(text) // 4 if text else 0

def calculate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for part in content:
                total += estimate_tokens(str(part))
    return total

def compact_context(messages: List[Dict[str, Any]], max_tokens: int = 4000) -> List[Dict[str, Any]]:
    current_tokens = calculate_messages_tokens(messages)
    if current_tokens <= max_tokens:
        return messages

    # Keep system message (0) and last user message (-1)
    if len(messages) <= 2:
        return messages

    system_msg = messages[0] if messages[0].get("role") == "system" else None
    start_idx = 1 if system_msg else 0
    recent_msg = messages[-1]

    middle_messages = messages[start_idx:-1]
    compacted_middle = []

    for msg in middle_messages:
        content = msg.get("content", "")
        role = msg.get("role", "user")

        if isinstance(content, str) and len(content) > 200:
            shortened = content[:100] + "... [truncated for context compaction] ... " + content[-100:]
            compacted_middle.append({"role": role, "content": shortened})
        else:
            compacted_middle.append(msg)

    result = []
    if system_msg:
        result.append(system_msg)

    result.extend(compacted_middle)
    result.append(recent_msg)

    return result
