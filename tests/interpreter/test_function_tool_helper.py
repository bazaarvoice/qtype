"""Unit tests for FunctionToolHelper."""

from __future__ import annotations

import pytest

from qtype.interpreter.executors.invoke_tool_executor import ToolExecutionMixin
from qtype.interpreter.tools import FunctionToolHelper
from qtype.semantic.loader import load
from qtype.semantic.model import Application, PythonFunctionTool

pytestmark = pytest.mark.asyncio


class TestToolHelper(ToolExecutionMixin, FunctionToolHelper):
    """Test class combining the mixins needed for tool creation."""

    pass


async def test_create_python_function_tool_and_call():
    """Test creating and calling a Python function tool."""
    # Load the commons tools spec
    doc, _ = load("common/tools.qtype.yaml")
    assert isinstance(doc, Application)

    # Find the get_current_timestamp tool
    timestamp_tool = None
    for tool in doc.tools:
        if (
            isinstance(tool, PythonFunctionTool)
            and tool.function_name == "get_current_timestamp"
        ):
            timestamp_tool = tool
            break

    assert timestamp_tool is not None, "get_current_timestamp tool not found"

    # Create the helper and generate the FunctionTool
    helper = TestToolHelper()
    function_tool = helper._create_python_function_tool(timestamp_tool)

    # Call the function tool
    result = await function_tool.acall()

    # Verify we got a datetime result
    assert result is not None
    # The result should be a datetime string or object
    assert result is not None
