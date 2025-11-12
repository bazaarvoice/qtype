"""Unit tests for step executor caching."""

from __future__ import annotations

import uuid
from typing import AsyncIterator

import pytest

from qtype.base.types import CacheConfig
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.secrets import NoOpSecretManager
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Step

pytestmark = pytest.mark.asyncio


class CacheTestStep(Step):
    type: str = "CacheTestStep"


class ProcessingExecutor(StepExecutor):
    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        yield message.copy_with_variables({"result": "processed"})


class FailingExecutor(StepExecutor):
    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        raise RuntimeError("Should not be called")
        yield  # type: ignore[unreachable]


async def test_cache_hit():
    """Test that cached results are returned without re-executing."""

    step_id = str(uuid.uuid4())
    cache_config = CacheConfig(namespace="test")
    step = CacheTestStep(id=step_id, cache_config=cache_config)
    context = ExecutorContext(secret_manager=NoOpSecretManager())
    message = FlowMessage(
        session=Session(session_id="test"), variables={"input": "test"}
    )

    # First execution - populate cache
    executor = ProcessingExecutor(step, context)

    async def message_stream():
        yield message

    results = [msg async for msg in executor.execute(message_stream())]
    assert len(results) == 1
    assert results[0].variables["result"] == "processed"

    # Second execution with failing executor - should use cache and not fail
    step2 = CacheTestStep(id=step_id, cache_config=cache_config)
    executor2 = FailingExecutor(step2, context)

    results2 = [msg async for msg in executor2.execute(message_stream())]
    assert len(results2) == 1
    assert results2[0].variables["result"] == "processed"
