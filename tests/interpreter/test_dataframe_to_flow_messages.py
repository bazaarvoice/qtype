"""Tests for dataframe_to_flow_messages converter."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import SearchResult
from qtype.interpreter.converters import dataframe_to_flow_messages
from qtype.semantic.loader import load
from qtype.semantic.model import Variable


def test_dataframe_to_flow_messages_with_primitives():
    """Test converting DataFrame with primitive types to FlowMessages."""
    # Create DataFrame with primitive types
    df = pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "name": ["Alice", "Bob", "Carol"],
            "age": ["30", "25", "35"],
            "score": ["95.5", "87.3", "92.1"],
        }
    )

    # Define variables
    variables = [
        Variable(id="id", type=PrimitiveTypeEnum.int),
        Variable(id="name", type=PrimitiveTypeEnum.text),
        Variable(id="age", type=PrimitiveTypeEnum.int),
        Variable(id="score", type=PrimitiveTypeEnum.float),
    ]

    # Convert to FlowMessages
    messages = dataframe_to_flow_messages(df, variables)

    # Verify we got 3 messages
    assert len(messages) == 3

    # Check first message
    first_vars = messages[0].variables
    assert first_vars["id"] == 1
    assert isinstance(first_vars["id"], int)
    assert first_vars["name"] == "Alice"
    assert isinstance(first_vars["name"], str)
    assert first_vars["age"] == 30
    assert isinstance(first_vars["age"], int)
    assert first_vars["score"] == 95.5
    assert isinstance(first_vars["score"], float)

    # Check second message
    second_vars = messages[1].variables
    assert second_vars["id"] == 2
    assert second_vars["name"] == "Bob"
    assert second_vars["age"] == 25
    assert second_vars["score"] == 87.3

    # Check third message
    third_vars = messages[2].variables
    assert third_vars["id"] == 3
    assert third_vars["name"] == "Carol"
    assert third_vars["age"] == 35
    assert third_vars["score"] == 92.1


def test_dataframe_to_flow_messages_with_domain_type():
    """Test converting DataFrame with domain type cells to FlowMessages.

    This simulates reading from parquet where SearchResult instances were
    persisted as dicts via model_dump().
    """
    # Create SearchResult instances and dump to dicts (as would happen in parquet)
    result1 = SearchResult(
        content="Found relevant information about Python",
        doc_id="doc-123",
        score=0.95,
    )
    result2 = SearchResult(
        content="Another search result about testing",
        doc_id="doc-456",
        score=0.87,
    )
    result3 = SearchResult(
        content="Third result with lower relevance",
        doc_id="doc-789",
        score=0.72,
    )

    # Create DataFrame with dict cells (as read from parquet)
    df = pd.DataFrame(
        {
            "result": [
                result1.model_dump(),
                result2.model_dump(),
                result3.model_dump(),
            ]
        }
    )

    # Define variables - result should be converted to SearchResult
    variables = [Variable(id="result", type=SearchResult)]

    # Convert to FlowMessages
    messages = dataframe_to_flow_messages(df, variables)

    # Verify we got 3 messages
    assert len(messages) == 3

    # Check first message - should have SearchResult instance
    first_result = messages[0].variables["result"]
    assert isinstance(first_result, SearchResult)
    assert first_result.content == "Found relevant information about Python"
    assert first_result.doc_id == "doc-123"
    assert first_result.score == 0.95

    # Check second message
    second_result = messages[1].variables["result"]
    assert isinstance(second_result, SearchResult)
    assert second_result.content == "Another search result about testing"
    assert second_result.doc_id == "doc-456"
    assert second_result.score == 0.87

    # Check third message
    third_result = messages[2].variables["result"]
    assert isinstance(third_result, SearchResult)
    assert third_result.content == "Third result with lower relevance"
    assert third_result.doc_id == "doc-789"
    assert third_result.score == 0.72


def test_dataframe_to_flow_messages_with_custom_type():
    """Test converting DataFrame with custom type cells to FlowMessages.

    This simulates reading from CSV/parquet where custom type instances were
    persisted as dicts via model_dump().
    """
    # Load the custom type from spec
    spec_path = Path("tests/specs/file_source_custom_types.qtype.yaml")
    semantic_model, type_registry = load(spec_path)

    # Get the Person type from the registry
    Person = type_registry["Person"]

    # Create Person instances and dump to dicts (as would happen in CSV/parquet)
    person1 = Person(name="Alice Johnson", age=30, email="alice@example.com")
    person2 = Person(name="Bob Smith", age=25, email="bob@example.com")
    person3 = Person(name="Carol Davis", age=35, email="carol@example.com")

    # Create DataFrame with dict cells (as read from CSV/parquet)
    df = pd.DataFrame(
        {
            "person": [
                person1.model_dump(),
                person2.model_dump(),
                person3.model_dump(),
            ]
        }
    )

    # Define variables - person should be converted to Person type
    variables = [Variable(id="person", type=Person)]

    # Convert to FlowMessages
    messages = dataframe_to_flow_messages(df, variables)

    # Verify we got 3 messages
    assert len(messages) == 3

    # Check first message - should have Person instance
    first_person = messages[0].variables["person"]
    assert isinstance(first_person, Person)
    assert first_person.name == "Alice Johnson"
    assert first_person.age == 30
    assert first_person.email == "alice@example.com"

    # Check second message
    second_person = messages[1].variables["person"]
    assert isinstance(second_person, Person)
    assert second_person.name == "Bob Smith"
    assert second_person.age == 25
    assert second_person.email == "bob@example.com"

    # Check third message
    third_person = messages[2].variables["person"]
    assert isinstance(third_person, Person)
    assert third_person.name == "Carol Davis"
    assert third_person.age == 35
    assert third_person.email == "carol@example.com"
