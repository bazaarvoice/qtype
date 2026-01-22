"""Tests for the Echo step executor."""

import pytest

from qtype.interpreter.executors.echo_executor import EchoExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Echo, Variable

pytestmark = pytest.mark.asyncio


async def test_echo_passes_through_variables(executor_context):
    """Test that Echo step passes through all input variables to outputs."""
    # Create variables
    var1 = Variable(id="test_var1", type="text")
    var2 = Variable(id="test_var2", type="int")

    # Create Echo step
    echo_step = Echo(
        id="echo_test",
        type="Echo",
        inputs=[var1, var2],
        outputs=[var1, var2],
    )

    # Create executor
    executor = EchoExecutor(echo_step, executor_context)

    # Create test message with variable values
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={
            "test_var1": "Hello, World!",
            "test_var2": 42,
        },
    )

    # Execute the echo step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify results
    assert len(results) == 1
    result = results[0]

    # Check that variables were echoed
    assert result.variables["test_var1"] == "Hello, World!"
    assert result.variables["test_var2"] == 42


async def test_echo_handles_different_order(executor_context):
    """Test that Echo works with inputs and outputs in different order."""
    # Create variables in different order
    var1 = Variable(id="var_a", type="text")
    var2 = Variable(id="var_b", type="int")

    # Create Echo step with different order for outputs
    echo_step = Echo(
        id="echo_test",
        type="Echo",
        inputs=[var1, var2],
        outputs=[var2, var1],  # Different order
    )

    # Create executor
    executor = EchoExecutor(echo_step, executor_context)

    # Create test message with variable values
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={
            "var_a": "test value",
            "var_b": 100,
        },
    )

    # Execute the echo step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify results
    assert len(results) == 1
    result = results[0]

    # Check that variables were echoed correctly
    assert result.variables["var_a"] == "test value"
    assert result.variables["var_b"] == 100


async def test_echo_with_missing_variable(executor_context):
    """Test that Echo handles missing variables gracefully."""
    # Create variables
    var1 = Variable(id="present_var", type="text")
    var2 = Variable(id="missing_var", type="int")

    # Create Echo step
    echo_step = Echo(
        id="echo_test",
        type="Echo",
        inputs=[var1, var2],
        outputs=[var1, var2],
    )

    # Create executor
    executor = EchoExecutor(echo_step, executor_context)

    # Create test message with only one variable
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={
            "present_var": "I exist!",
            # missing_var is not present
        },
    )

    # Execute the echo step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify results
    assert len(results) == 1
    result = results[0]

    # Check that present variable was echoed
    assert result.variables["present_var"] == "I exist!"
    # Missing variable should be None
    assert result.variables.get("missing_var") is None
