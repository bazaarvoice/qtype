"""Tests for FileSource executor."""

from __future__ import annotations

from pathlib import Path

import pytest

from qtype.dsl.domain_types import SearchResult
from qtype.interpreter.executors.file_source_executor import FileSourceExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.loader import load


@pytest.mark.asyncio
async def test_file_source_loads_custom_types(executor_context):
    """Test that FileSource can load JSON with mixed types: custom, domain, and primitive."""
    # Load the spec with custom Person type
    spec_path = Path("tests/specs/file_source_custom_types.qtype.yaml")
    semantic_model, type_registry = load(spec_path)

    # Get the Person type and the flow
    Person = type_registry["Person"]
    flow = semantic_model.flows[0]
    file_source_step = flow.steps[0]

    # Create FileSource executor
    executor = FileSourceExecutor(file_source_step, executor_context)

    # Create an initial flow message
    initial_message = FlowMessage(
        session=Session(session_id="test"), variables={}
    )

    # Execute the FileSource step
    results = []
    async for result_message in executor.process_message(initial_message):
        results.append(result_message)

    # Validate we got 3 results (one per row in the JSON)
    assert len(results) == 3

    # Validate first row has all three types correctly
    first_vars = results[0].variables

    # Check Person (custom type)
    first_person = first_vars["person"]
    assert isinstance(first_person, Person)
    assert first_person.name == "Alice Johnson"
    assert first_person.age == 30
    assert first_person.email == "alice@example.com"

    # Check SearchResult (domain type)
    first_result = first_vars["result"]
    assert isinstance(first_result, SearchResult)
    assert first_result.content == "Found information about Python"
    assert first_result.doc_id == "doc-123"
    assert abs(first_result.score - 0.95) < 0.01

    # Check rank (primitive int type)
    first_rank = first_vars["rank"]
    assert isinstance(first_rank, int)
    assert first_rank == 1

    # Validate second row
    second_vars = results[1].variables
    assert isinstance(second_vars["person"], Person)
    assert second_vars["person"].name == "Bob Smith"
    assert isinstance(second_vars["result"], SearchResult)
    assert second_vars["result"].doc_id == "doc-456"
    assert isinstance(second_vars["rank"], int)
    assert second_vars["rank"] == 2

    # Validate third row
    third_vars = results[2].variables
    assert isinstance(third_vars["person"], Person)
    assert third_vars["person"].name == "Carol Davis"
    assert isinstance(third_vars["result"], SearchResult)
    assert third_vars["result"].doc_id == "doc-789"
    assert isinstance(third_vars["rank"], int)
    assert third_vars["rank"] == 3
