"""Unit tests for flow execution."""

from __future__ import annotations

from typing import AsyncIterator

import pytest

from qtype.base.types import PrimitiveTypeEnum
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.secrets import NoOpSecretManager
from qtype.interpreter.flow import run_flow
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Echo, Flow, Variable

pytestmark = pytest.mark.asyncio


class SourceTestStep(Echo):
    """Test step that generates output without requiring inputs."""

    type: str = "SourceTestStep"
    inputs: list[Variable] = []
    outputs: list[Variable] = [
        Variable(id="generated", type=PrimitiveTypeEnum.text)
    ]


class SourceExecutor(StepExecutor):
    """Executor that generates data without requiring input variables."""

    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        # Source steps generate data regardless of input variables
        yield message.copy_with_variables({"generated": "source_data"})


async def test_flow_with_no_inputs_executes():
    """Test that a flow with no inputs still executes source steps."""
    # Create a flow with no inputs but with a source step
    source_step = SourceTestStep(id="source", type="SourceTestStep")
    flow = Flow(
        id="test_flow",
        type="Flow",
        description="Flow with no inputs",
        inputs=[],
        outputs=[Variable(id="generated", type=PrimitiveTypeEnum.text)],
        steps=[source_step],
    )

    # Register the executor for our test step
    from qtype.interpreter.base import factory

    original_create = factory.create_executor

    def mock_create(step, context, **kwargs):
        if isinstance(step, SourceTestStep):
            return SourceExecutor(step, context)
        return original_create(step, context, **kwargs)

    factory.create_executor = mock_create

    try:
        context = ExecutorContext(secret_manager=NoOpSecretManager())

        # Run with empty list - should create an empty message automatically
        results = await run_flow(flow, [], context=context)

        # Verify the source step executed and produced output
        assert len(results) == 1
        assert not results[0].is_failed()
        assert results[0].variables["generated"] == "source_data"
    finally:
        factory.create_executor = original_create


async def test_flow_with_empty_message():
    """Test that a flow can be executed with an explicit empty message."""
    source_step = SourceTestStep(id="source", type="SourceTestStep")
    flow = Flow(
        id="test_flow",
        type="Flow",
        description="Flow with empty message",
        inputs=[],
        outputs=[Variable(id="generated", type=PrimitiveTypeEnum.text)],
        steps=[source_step],
    )

    from qtype.interpreter.base import factory

    original_create = factory.create_executor

    def mock_create(step, context, **kwargs):
        if isinstance(step, SourceTestStep):
            return SourceExecutor(step, context)
        return original_create(step, context, **kwargs)

    factory.create_executor = mock_create

    try:
        context = ExecutorContext(secret_manager=NoOpSecretManager())

        # Create an empty message explicitly
        empty_message = FlowMessage(
            session=Session(session_id="test"),
            variables={},
        )

        results = await run_flow(flow, empty_message, context=context)

        assert len(results) == 1
        assert not results[0].is_failed()
        assert results[0].variables["generated"] == "source_data"
    finally:
        factory.create_executor = original_create


async def test_flow_preserves_session_id_in_empty_message():
    """Test that session_id from kwargs is preserved in auto-created empty message."""
    source_step = SourceTestStep(id="source", type="SourceTestStep")
    flow = Flow(
        id="test_flow",
        type="Flow",
        description="Flow with session",
        inputs=[],
        outputs=[Variable(id="generated", type=PrimitiveTypeEnum.text)],
        steps=[source_step],
    )

    from qtype.interpreter.base import factory

    original_create = factory.create_executor

    def mock_create(step, context, **kwargs):
        if isinstance(step, SourceTestStep):
            return SourceExecutor(step, context)
        return original_create(step, context, **kwargs)

    factory.create_executor = mock_create

    try:
        context = ExecutorContext(secret_manager=NoOpSecretManager())

        # Run with empty list and custom session_id
        results = await run_flow(
            flow, [], context=context, session_id="custom_session"
        )

        assert len(results) == 1
        assert results[0].session.session_id == "custom_session"
    finally:
        factory.create_executor = original_create
