"""Tests for FieldExtractor executor."""

import pytest

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import RAGDocument
from qtype.interpreter.executors.field_extractor_executor import (
    FieldExtractorExecutor,
)
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import FieldExtractor, Variable

pytestmark = pytest.mark.asyncio


async def test_field_extractor_single_value(
    executor_context,
):
    """Test extracting a single field from input."""
    # Create a FieldExtractor step
    input_var = Variable(id="input_data", type=PrimitiveTypeEnum.text)
    output_var = Variable(id="output_name", type=PrimitiveTypeEnum.text)

    step = FieldExtractor(
        id="extract_name",
        type="FieldExtractor",
        json_path="$.name",
        inputs=[input_var],
        outputs=[output_var],
    )

    # Create executor
    executor = FieldExtractorExecutor(step, executor_context)

    # Create input message with dict data
    input_data = {"name": "John Doe", "age": 30}
    message = FlowMessage(
        session=Session(session_id="test"),
        variables={"input_data": input_data},
    )

    # Process message
    results = []
    async for result in executor.process_message(message):
        results.append(result)

    # Should yield one result
    assert len(results) == 1
    assert not results[0].is_failed()
    assert results[0].variables["output_name"] == "John Doe"


async def test_field_extractor_multiple_values(
    executor_context,
):
    """Test extracting multiple values (1-to-many)."""
    # Create a FieldExtractor step
    input_var = Variable(id="input_data", type=PrimitiveTypeEnum.text)
    output_var = Variable(id="item", type=PrimitiveTypeEnum.text)

    step = FieldExtractor(
        id="extract_items",
        type="FieldExtractor",
        json_path="$.items[*]",
        inputs=[input_var],
        outputs=[output_var],
    )

    # Create executor
    executor = FieldExtractorExecutor(step, executor_context)

    # Create input message with list data
    input_data = {"items": ["apple", "banana", "cherry"]}
    message = FlowMessage(
        session=Session(session_id="test"),
        variables={"input_data": input_data},
    )

    # Process message
    results = []
    async for result in executor.process_message(message):
        results.append(result)

    # Should yield three results (one per item)
    assert len(results) == 3
    assert all(not r.is_failed() for r in results)
    assert results[0].variables["item"] == "apple"
    assert results[1].variables["item"] == "banana"
    assert results[2].variables["item"] == "cherry"


async def test_field_extractor_with_pydantic_model(
    executor_context,
):
    """Test extracting from a Pydantic model input."""
    # Create a FieldExtractor step
    input_var = Variable(id="doc", type=RAGDocument)
    output_var = Variable(id="file_name", type=PrimitiveTypeEnum.text)

    step = FieldExtractor(
        id="extract_filename",
        type="FieldExtractor",
        json_path="$.file_name",
        inputs=[input_var],
        outputs=[output_var],
    )

    # Create executor
    executor = FieldExtractorExecutor(step, executor_context)

    # Create input message with RAGDocument
    doc = RAGDocument(
        file_id="doc1",
        file_name="test.txt",
        content="Sample content",
        uri="file:///test.txt",
        type=PrimitiveTypeEnum.text,
        metadata={},
    )
    message = FlowMessage(
        session=Session(session_id="test"),
        variables={"doc": doc},
    )

    # Process message
    results = []
    async for result in executor.process_message(message):
        results.append(result)

    # Should yield one result
    assert len(results) == 1
    assert not results[0].is_failed()
    assert results[0].variables["file_name"] == "test.txt"


async def test_field_extractor_no_match(
    executor_context,
):
    """Test that an error is raised when JSONPath doesn't match."""
    # Create a FieldExtractor step
    input_var = Variable(id="input_data", type=PrimitiveTypeEnum.text)
    output_var = Variable(id="output_value", type=PrimitiveTypeEnum.text)

    step = FieldExtractor(
        id="extract_missing",
        type="FieldExtractor",
        json_path="$.nonexistent",
        inputs=[input_var],
        outputs=[output_var],
    )

    # Create executor
    executor = FieldExtractorExecutor(step, executor_context)

    # Create input message
    input_data = {"name": "John"}
    message = FlowMessage(
        session=Session(session_id="test"),
        variables={"input_data": input_data},
    )

    # Process message
    results = []
    async for result in executor.process_message(message):
        results.append(result)

    # Should yield one error result
    assert len(results) == 1
    assert results[0].is_failed()
    assert "did not match any data" in str(results[0].error)
