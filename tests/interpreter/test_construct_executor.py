"""Tests for the Construct step executor."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import RAGChunk
from qtype.dsl.model import ListType
from qtype.interpreter.executors.construct_executor import ConstructExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Construct, Variable

pytestmark = pytest.mark.asyncio


class CustomTypeForTest(BaseModel):
    """Custom type for testing construct executor."""

    name: str = Field(..., description="The name")
    score: float = Field(..., description="The score")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


async def test_construct_primitive_type(executor_context):
    """Test constructing a primitive type (float)."""
    # Create variables
    input_var = Variable(id="value_str", type=PrimitiveTypeEnum.text)
    output_var = Variable(id="value_float", type=PrimitiveTypeEnum.float)

    # Create Construct step
    construct_step = Construct(
        id="construct_float",
        type="Construct",
        inputs=[input_var],
        outputs=[output_var],
        field_mapping={},
    )

    # Create executor
    executor = ConstructExecutor(construct_step, executor_context)

    # Create test message
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={"value_str": "42.5"},
    )

    # Execute the construct step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify
    assert len(results) == 1
    assert results[0].variables["value_float"] == 42.5
    assert isinstance(results[0].variables["value_float"], float)


async def test_construct_list_type(executor_context):
    """Test constructing a list type."""
    # Create variables
    input_var = Variable(
        id="items_input", type=PrimitiveTypeEnum.text, value=None
    )
    output_var = Variable(
        id="items_list",
        type=ListType(element_type=PrimitiveTypeEnum.int),
    )

    # Create Construct step
    construct_step = Construct(
        id="construct_list",
        type="Construct",
        inputs=[input_var],
        outputs=[output_var],
        field_mapping={},
    )

    # Create executor
    executor = ConstructExecutor(construct_step, executor_context)

    # Create test message
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={"items_input": [1, 2, 3, 4, 5]},
    )

    # Execute the construct step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify
    assert len(results) == 1
    assert results[0].variables["items_list"] == [1, 2, 3, 4, 5]
    assert isinstance(results[0].variables["items_list"], list)


async def test_construct_domain_type(executor_context):
    """Test constructing a domain type (RAGChunk)."""
    # Create variables
    chunk_id_var = Variable(id="chunk_id", type=PrimitiveTypeEnum.text)
    doc_id_var = Variable(id="doc_id", type=PrimitiveTypeEnum.text)
    content_var = Variable(id="content", type=PrimitiveTypeEnum.text)
    output_var = Variable(id="rag_chunk", type=RAGChunk)

    # Create Construct step with field mapping
    construct_step = Construct(
        id="construct_rag_chunk",
        type="Construct",
        inputs=[chunk_id_var, doc_id_var, content_var],
        outputs=[output_var],
        field_mapping={
            "chunk_id": "chunk_id",
            "doc_id": "document_id",
            "content": "content",
        },
    )

    # Create executor
    executor = ConstructExecutor(construct_step, executor_context)

    # Create test message
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={
            "chunk_id": "chunk-123",
            "doc_id": "doc-456",
            "content": "Sample chunk content",
        },
    )

    # Execute the construct step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify
    assert len(results) == 1
    rag_chunk = results[0].variables["rag_chunk"]
    assert isinstance(rag_chunk, RAGChunk)
    assert rag_chunk.chunk_id == "chunk-123"
    assert rag_chunk.document_id == "doc-456"
    assert rag_chunk.content == "Sample chunk content"


async def test_construct_custom_type(executor_context):
    """Test constructing a custom type (CustomTypeForTest)."""
    # Create variables
    name_var = Variable(id="name", type=PrimitiveTypeEnum.text)
    score_var = Variable(id="score", type=PrimitiveTypeEnum.float)
    output_var = Variable(id="custom_obj", type=CustomTypeForTest)

    # Create Construct step with field mapping
    construct_step = Construct(
        id="construct_custom",
        type="Construct",
        inputs=[name_var, score_var],
        outputs=[output_var],
        field_mapping={
            "name": "name",
            "score": "score",
        },
    )

    # Create executor
    executor = ConstructExecutor(construct_step, executor_context)

    # Create test message
    session = Session(session_id="test-session")
    message = FlowMessage(
        session=session,
        variables={
            "name": "Test Item",
            "score": 95.5,
        },
    )

    # Execute the construct step
    results = []
    async for result_msg in executor.process_message(message):
        results.append(result_msg)

    # Verify
    assert len(results) == 1
    custom_obj = results[0].variables["custom_obj"]
    assert isinstance(custom_obj, CustomTypeForTest)
    assert custom_obj.name == "Test Item"
    assert custom_obj.score == 95.5
    assert custom_obj.tags == []  # Default empty list
