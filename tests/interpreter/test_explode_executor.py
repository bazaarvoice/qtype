"""Tests for the Explode step executor."""

from __future__ import annotations

import pytest

from qtype.interpreter.executors.explode_executor import ExplodeExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Explode, Variable

pytestmark = pytest.mark.asyncio


async def test_explode_emits_n_messages_with_matching_references(
    executor_context,
):
    """Test that Explode emits N messages with matching references."""
    # Create variables
    input_var = Variable(id="items", type="list", value=None)
    output_var = Variable(id="item", type="text", value=None)

    # Create Explode step
    explode_step = Explode(
        id="explode_test",
        type="Explode",
        inputs=[input_var],
        outputs=[output_var],
    )

    # Create executor
    executor = ExplodeExecutor(explode_step, executor_context)

    # Create test message with list of items
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={"items": ["apple", "banana", "cherry"]},
    )

    # Execute the explode step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify N messages emitted
    assert len(results) == 3

    # Verify each message has correct reference and output
    assert results[0].variables["item"] == "apple"
    assert results[1].variables["item"] == "banana"
    assert results[2].variables["item"] == "cherry"

    # Verify all messages share same session reference
    assert all(msg.session == session for msg in results)
