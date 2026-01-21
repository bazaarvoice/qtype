"""Tests for the Collect step executor."""

from __future__ import annotations

import pytest

from qtype.interpreter.executors.collect_executor import CollectExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Collect, Variable

pytestmark = pytest.mark.asyncio


async def test_collect_emits_single_list_with_common_ancestors(
    executor_context,
):
    """Test that Collect emits one list and propagates only common ancestors."""
    # Create variables
    input_var = Variable(id="item", type="text", value=None)
    output_var = Variable(id="items", type="list[text]", value=None)

    # Create Collect step
    collect_step = Collect(
        id="collect_test",
        type="Collect",
        inputs=[input_var],
        outputs=[output_var],
    )

    # Create executor
    executor = CollectExecutor(collect_step, executor_context)

    # Create test messages with mix of common and uncommon ancestors
    session = Session(session_id="test-session")
    messages = [
        FlowMessage(
            session=session,
            variables={
                "item": "apple",
                "common_var": "shared_value",
                "unique_to_first": "x",
            },
        ),
        FlowMessage(
            session=session,
            variables={
                "item": "banana",
                "common_var": "shared_value",
                "unique_to_second": "y",
            },
        ),
        FlowMessage(
            session=session,
            variables={
                "item": "cherry",
                "common_var": "shared_value",
                "unique_to_third": "z",
            },
        ),
    ]

    # Execute the collect step
    results = []
    async for result_msg in executor.process_batch(messages):
        results.append(result_msg)

    # Verify only one message emitted
    assert len(results) == 1

    # Verify output list contains all items
    assert results[0].variables["items"] == ["apple", "banana", "cherry"]

    # Verify only common ancestors are propagated
    assert results[0].variables["common_var"] == "shared_value"
    assert "unique_to_first" not in results[0].variables
    assert "unique_to_second" not in results[0].variables
    assert "unique_to_third" not in results[0].variables
