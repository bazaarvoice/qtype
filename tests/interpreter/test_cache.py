"""Unit tests for step executor caching."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import AsyncIterator

import pytest

from qtype.base.types import CacheConfig, PrimitiveTypeEnum
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.secrets import NoOpSecretManager
from qtype.interpreter.converters import (
    dataframe_to_flow_messages,
    flow_messages_to_dataframe,
)
from qtype.interpreter.flow import run_flow
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.loader import load
from qtype.semantic.model import Step, Variable

pytestmark = pytest.mark.asyncio


class CacheTestStep(Step):
    type: str = "CacheTestStep"
    inputs: list[Variable] = [
        Variable(id="input", type=PrimitiveTypeEnum.text)
    ]
    outputs: list[Variable] = [
        Variable(id="result", type=PrimitiveTypeEnum.text)
    ]


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


class ErroringExecutor(StepExecutor):
    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        yield message.copy_with_error(self.step.id, Exception("error"))


async def test_cache_on_error():
    """Test that error results are cached when on_error is 'Cache'."""
    step_id = str(uuid.uuid4())
    cache_config = CacheConfig(namespace="test", on_error="Cache")
    step = CacheTestStep(id=step_id, cache_config=cache_config)
    context = ExecutorContext(secret_manager=NoOpSecretManager())
    message = FlowMessage(
        session=Session(session_id="test"), variables={"input": "test"}
    )

    # First execution - should yield an error and cache it
    executor = ErroringExecutor(step, context)

    async def message_stream():
        yield message

    results = [msg async for msg in executor.execute(message_stream())]
    assert len(results) == 1
    assert results[0].is_failed()

    # Second execution with failing executor - should use cache and not raise
    step2 = CacheTestStep(id=step_id, cache_config=cache_config)
    executor2 = FailingExecutor(step2, context)

    results2 = [msg async for msg in executor2.execute(message_stream())]
    assert len(results2) == 1
    assert results2[0].is_failed()


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


async def test_cache_includes_referenced_variables_outside_inputs():
    """Test that cache key includes variables referenced outside inputs (issue #98).

    FileSource references the path variable which may not be in the inputs list.
    The cache key must include this variable, otherwise different file paths
    incorrectly share the same cache entry.
    """
    import pandas as pd

    test_dir = Path(__file__).parent
    yaml_file = test_dir / "test_cache_filesource.qtype.yaml"
    file1_path = str(test_dir / "test_file1.csv")
    file2_path = str(test_dir / "test_file2.csv")

    # Load the semantic model
    semantic_model, _ = load(yaml_file)
    flow = semantic_model.flows[0]
    context = ExecutorContext(secret_manager=NoOpSecretManager())

    # First execution with file1
    input_df1 = pd.DataFrame([{"file_path": file1_path}])
    messages1 = dataframe_to_flow_messages(
        input_df1, flow.inputs, session=Session(session_id="test")
    )
    results1 = await run_flow(flow, messages1, context=context)
    result_df1 = flow_messages_to_dataframe(results1, flow)
    assert result_df1["data"][0] == "file1_data"

    # Second execution with file2 should NOT use cached result from file1
    input_df2 = pd.DataFrame([{"file_path": file2_path}])
    messages2 = dataframe_to_flow_messages(
        input_df2, flow.inputs, session=Session(session_id="test")
    )
    results2 = await run_flow(flow, messages2, context=context)
    result_df2 = flow_messages_to_dataframe(results2, flow)
    assert result_df2["data"][0] == "file2_data", (
        "Cache should not be shared between different file paths"
    )
