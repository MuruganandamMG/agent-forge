import pytest
from google.genai import types
from runtime.tools.base import Tool, ToolResult, tool_registry, tool

def test_tool_result_defaults():
    res = ToolResult(success=True, output="hello")
    assert res.success is True
    assert res.output == "hello"
    assert res.error is None

@tool(description="A test math tool")
def add_numbers(a: int, b: int) -> int:
    return a + b

def test_tool_decorator_registers_function():
    assert "add_numbers" in tool_registry
    registered = tool_registry["add_numbers"]
    assert isinstance(registered, Tool)
    assert registered.name == "add_numbers"
    assert registered.description == "A test math tool"

def test_tool_to_genai_declaration():
    registered = tool_registry["add_numbers"]
    decl = registered.to_genai_declaration()
    assert isinstance(decl, types.FunctionDeclaration)
    assert decl.name == "add_numbers"

def test_tool_execution():
    registered = tool_registry["add_numbers"]
    result = registered.execute(a=5, b=10)
    assert result.success is True
    assert result.output == "15"
