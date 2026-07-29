import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from google.genai import types

@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None

tool_registry: Dict[str, "Tool"] = {}

class Tool:
    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""

    def execute(self, **kwargs) -> ToolResult:
        try:
            res = self.func(**kwargs)
            if isinstance(res, ToolResult):
                return res
            return ToolResult(success=True, output=str(res))
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def to_genai_declaration(self) -> types.FunctionDeclaration:
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = param.annotation
            type_str = "STRING"
            if param_type == int:
                type_str = "INTEGER"
            elif param_type == float:
                type_str = "NUMBER"
            elif param_type == bool:
                type_str = "BOOLEAN"

            properties[param_name] = types.Schema(type=type_str)
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        parameters_schema = types.Schema(
            type="OBJECT",
            properties=properties,
            required=required if required else None
        )

        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=parameters_schema
        )

def tool(name: Optional[str] = None, description: Optional[str] = None):
    def decorator(func: Callable):
        t = Tool(func, name=name, description=description)
        tool_registry[t.name] = t
        return func
    return decorator
