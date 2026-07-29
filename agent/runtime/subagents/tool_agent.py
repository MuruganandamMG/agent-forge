from typing import Any, List, Optional
from google.genai import types
from runtime.providers.gemini_provider import GeminiProvider
from runtime.tools.base import Tool, tool_registry
from runtime.ui import render_subagent_card

def _normalize_tool(t: Any) -> Tool:
    if isinstance(t, Tool):
        return t
    if callable(t):
        name = getattr(t, "__name__", str(t))
        if name in tool_registry:
            return tool_registry[name]
        return Tool(t)
    raise ValueError(f"Invalid tool type: {type(t)}")

def run_tool_agent(
    task_desc: str,
    tools: Optional[List[Any]] = None,
    provider: Optional[Any] = None,
    max_turns: int = 10,
    system_prompt: str = "You are an expert autonomous coding agent. Use available tools to solve the user's task."
) -> str:
    if provider is None:
        provider = GeminiProvider()

    if tools is None:
        normalized_tools = list(tool_registry.values())
    else:
        normalized_tools = [_normalize_tool(t) for t in tools]

    tool_map = {t.name: t for t in normalized_tools}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_desc}
    ]

    for turn in range(max_turns):
        text, function_calls = provider.chat_with_tools(messages=messages, tools=normalized_tools)

        if not function_calls:
            return text

        # Execute function calls
        parts = []
        if text:
            parts.append(types.Part.from_text(text=text))

        for fc in function_calls:
            tool_name = fc.name
            tool_args = fc.args or {}

            render_subagent_card(f"🛠️ Executing Tool: {tool_name}", str(tool_args), border_style="blue")

            if tool_name in tool_map:
                tool_res = tool_map[tool_name].execute(**tool_args)
                result_str = tool_res.output if tool_res.success else f"Error: {tool_res.error}"
            else:
                result_str = f"Error: Tool {tool_name} not found"

            render_subagent_card(f"📋 Tool Result: {tool_name}", result_str[:1000], border_style="dim blue")

            parts.append(types.Part.from_function_response(
                name=tool_name,
                response={"result": result_str}
            ))

        messages.append({"role": "assistant", "parts": parts})

    return "Task ended: reached maximum tool turns."
