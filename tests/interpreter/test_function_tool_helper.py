"""Unit tests for FunctionToolHelper."""

from __future__ import annotations

import pytest

from qtype.interpreter.executors.invoke_tool_executor import ToolExecutionMixin
from qtype.interpreter.tools import FunctionToolHelper
from qtype.semantic.loader import load
from qtype.semantic.model import Application, PythonFunctionTool


class ToolHelper(ToolExecutionMixin, FunctionToolHelper):
    """Helper class combining the mixins needed for tool creation."""

    def __init__(self) -> None:
        # Initialize the mixins with minimal required attributes
        # Since this is a test helper, we can mock these
        from unittest.mock import MagicMock

        super().__init__()
        self.stream_emitter = MagicMock()
        self.step = MagicMock()


@pytest.mark.asyncio
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
    helper = ToolHelper()
    function_tool = helper._create_python_function_tool(timestamp_tool)

    # Call the function tool
    result = await function_tool.acall()

    # Verify we got a datetime result
    assert result is not None
    # The result should be a datetime string or object
    assert result is not None


def test_qtype_type_to_python_type_list():
    """Test that list types are correctly converted to typed lists."""
    from qtype.base.types import PrimitiveTypeEnum
    from qtype.dsl.model import ListType, ToolParameter

    # Test list[text] -> list[str]
    text_list_param = ToolParameter(
        type=ListType(element_type=PrimitiveTypeEnum.text),
        optional=False,
    )
    python_type = FunctionToolHelper._qtype_type_to_python_type(
        text_list_param
    )
    assert python_type == list[str]

    # Test list[int] -> list[int]
    int_list_param = ToolParameter(
        type=ListType(element_type=PrimitiveTypeEnum.int),
        optional=False,
    )
    python_type = FunctionToolHelper._qtype_type_to_python_type(int_list_param)
    assert python_type == list[int]

    # Test list[boolean] -> list[bool]
    bool_list_param = ToolParameter(
        type=ListType(element_type=PrimitiveTypeEnum.boolean),
        optional=False,
    )
    python_type = FunctionToolHelper._qtype_type_to_python_type(
        bool_list_param
    )
    assert python_type == list[bool]


@pytest.mark.asyncio
async def test_create_python_function_tool_with_custom_type():
    """Test creating and calling a tool that returns a custom type."""
    from datetime import datetime

    from pydantic import BaseModel

    # Load the commons tools spec
    doc, _ = load("common/tools.qtype.yaml")
    assert isinstance(doc, Application)

    # Find the calculate_time_difference tool
    time_diff_tool = None
    for tool in doc.tools:
        if (
            isinstance(tool, PythonFunctionTool)
            and tool.function_name == "calculate_time_difference"
        ):
            time_diff_tool = tool
            break

    assert time_diff_tool is not None, (
        "calculate_time_difference tool not found"
    )

    # Verify the output type is the custom TimeDifferenceResultType
    assert "result" in time_diff_tool.outputs
    output_param = time_diff_tool.outputs["result"]
    # The type should be resolved to a BaseModel subclass
    assert isinstance(output_param.type, type)
    assert issubclass(output_param.type, BaseModel)

    # Create the helper and generate the FunctionTool
    helper = ToolHelper()
    function_tool = helper._create_python_function_tool(time_diff_tool)

    # Call the function tool with two timestamps
    start = datetime(2024, 1, 1, 12, 0, 0)
    end = datetime(2024, 1, 2, 14, 30, 0)

    result = await function_tool.acall(start_time=start, end_time=end)

    # Verify we got a result with the expected structure
    assert result is not None
    # LlamaIndex wraps the result in a ToolOutput object
    assert hasattr(result, "raw_output")
    custom_type_result = result.raw_output

    # Verify the custom type has the expected fields
    assert hasattr(custom_type_result, "days")
    assert hasattr(custom_type_result, "seconds")
    assert hasattr(custom_type_result, "total_hours")
    # Use getattr for type checker compatibility
    assert getattr(custom_type_result, "days") == 1
    assert getattr(custom_type_result, "total_hours") == 26.5


@pytest.mark.asyncio
async def test_datetime_parameter_parsing_from_string():
    """Test that datetime parameters are parsed from strings (as LLMs pass).

    When an LLM calls a tool, it passes datetime values as ISO format
    strings. The Pydantic validation should automatically parse these
    strings into datetime objects before calling the function.
    """
    from datetime import datetime, timezone

    # Load the commons tools spec
    doc, _ = load("common/tools.qtype.yaml")
    assert isinstance(doc, Application)

    # Find the format_datetime tool
    format_tool = None
    for tool in doc.tools:
        if (
            isinstance(tool, PythonFunctionTool)
            and tool.function_name == "format_datetime"
        ):
            format_tool = tool
            break

    assert format_tool is not None, "format_datetime tool not found"

    # Create the helper and generate the FunctionTool
    helper = ToolHelper()
    function_tool = helper._create_python_function_tool(format_tool)

    # Call with a string timestamp (as an LLM would)
    result = await function_tool.acall(
        timestamp="2025-11-05 02:14:48.669534+00:00",
        format_string="%Y-%m-%dT%H:%M:%S.%fZ",
    )

    # Verify we got a properly formatted result
    assert result is not None
    assert hasattr(result, "raw_output")
    # The result should be a formatted string
    assert result.raw_output == "2025-11-05T02:14:48.669534Z"

    # Also test with a datetime object (should still work)
    dt = datetime(2025, 11, 5, 2, 14, 48, 669534, tzinfo=timezone.utc)
    result2 = await function_tool.acall(
        timestamp=dt,
        format_string="%Y-%m-%dT%H:%M:%S.%fZ",
    )

    assert result2 is not None
    assert hasattr(result2, "raw_output")
    assert result2.raw_output == "2025-11-05T02:14:48.669534Z"
