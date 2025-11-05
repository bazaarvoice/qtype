"""Tests for UI request to domain type conversions."""

from __future__ import annotations

import pytest

from qtype.base.types import PrimitiveTypeEnum
from qtype.interpreter.stream.chat.ui_request_to_domain_type import (
    _ui_message_to_domain_type,
    ui_request_to_domain_type,
)
from qtype.interpreter.stream.chat.vercel import (
    ChatRequest,
    ReasoningUIPart,
    SourceDocumentUIPart,
    SourceUrlUIPart,
    StepStartUIPart,
    TextUIPart,
    UIMessage,
)


def test_text_part_conversion():
    """Test conversion of text UI part to domain type."""
    message = UIMessage(
        id="msg-1",
        role="user",
        parts=[TextUIPart(text="Hello world", state="done")],
    )

    result = _ui_message_to_domain_type(message)

    assert result.role.value == "user"
    assert len(result.blocks) == 1
    assert result.blocks[0].type == PrimitiveTypeEnum.text
    assert result.blocks[0].content == "Hello world"


def test_reasoning_part_conversion():
    """Test conversion of reasoning UI part to domain type."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[ReasoningUIPart(text="Thinking step by step", state="done")],
    )

    result = _ui_message_to_domain_type(message)

    assert result.role.value == "assistant"
    assert len(result.blocks) == 1
    assert result.blocks[0].type == PrimitiveTypeEnum.text
    assert result.blocks[0].content == "Thinking step by step"


def test_source_url_part_conversion():
    """Test conversion of source URL UI part to domain type."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[
            SourceUrlUIPart(
                sourceId="source-1",
                url="https://example.com/doc",
                title="Example Document",
            )
        ],
    )

    result = _ui_message_to_domain_type(message)

    assert result.role.value == "assistant"
    assert len(result.blocks) == 1
    assert result.blocks[0].type == PrimitiveTypeEnum.citation_url
    assert result.blocks[0].content["source_id"] == "source-1"
    assert result.blocks[0].content["url"] == "https://example.com/doc"
    assert result.blocks[0].content["title"] == "Example Document"


def test_source_url_part_without_title():
    """Test conversion of source URL without title preserves None."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[
            SourceUrlUIPart(sourceId="source-1", url="https://example.com/doc")
        ],
    )

    result = _ui_message_to_domain_type(message)

    assert len(result.blocks) == 1
    assert result.blocks[0].type == PrimitiveTypeEnum.citation_url
    assert result.blocks[0].content["url"] == "https://example.com/doc"
    assert result.blocks[0].content["title"] is None


def test_source_document_part_conversion():
    """Test conversion of source document UI part to domain type."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[
            SourceDocumentUIPart(
                sourceId="doc-1",
                mediaType="application/pdf",
                title="Research Paper",
                filename="paper.pdf",
            )
        ],
    )

    result = _ui_message_to_domain_type(message)

    assert result.role.value == "assistant"
    assert len(result.blocks) == 1
    assert result.blocks[0].type == PrimitiveTypeEnum.citation_document
    assert result.blocks[0].content["source_id"] == "doc-1"
    assert result.blocks[0].content["title"] == "Research Paper"
    assert result.blocks[0].content["filename"] == "paper.pdf"
    assert result.blocks[0].content["media_type"] == "application/pdf"


def test_source_document_part_without_filename():
    """Test conversion of source document without filename preserves None."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[
            SourceDocumentUIPart(
                sourceId="doc-1",
                mediaType="application/pdf",
                title="Research Paper",
            )
        ],
    )

    result = _ui_message_to_domain_type(message)

    assert len(result.blocks) == 1
    assert result.blocks[0].type == PrimitiveTypeEnum.citation_document
    assert result.blocks[0].content["filename"] is None


def test_step_start_ignored():
    """Test that step-start parts are ignored (no content block)."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[
            StepStartUIPart(),
            TextUIPart(text="Step content", state="done"),
        ],
    )

    result = _ui_message_to_domain_type(message)

    # Step start should not create a block, only the text part
    assert len(result.blocks) == 1
    assert result.blocks[0].content == "Step content"


def test_multiple_parts_conversion():
    """Test conversion of message with multiple parts."""
    message = UIMessage(
        id="msg-1",
        role="assistant",
        parts=[
            TextUIPart(text="Here's what I found:", state="done"),
            SourceUrlUIPart(
                sourceId="src-1",
                url="https://example.com",
                title="Example",
            ),
            TextUIPart(text="Does this help?", state="done"),
        ],
    )

    result = _ui_message_to_domain_type(message)

    assert len(result.blocks) == 3
    assert result.blocks[0].type == PrimitiveTypeEnum.text
    assert result.blocks[0].content == "Here's what I found:"
    assert result.blocks[1].type == PrimitiveTypeEnum.citation_url
    assert result.blocks[1].content["url"] == "https://example.com"
    assert result.blocks[2].type == PrimitiveTypeEnum.text
    assert result.blocks[2].content == "Does this help?"


def test_empty_parts_raises_error():
    """Test that message with no valid content blocks raises error."""
    message = UIMessage(
        id="msg-1",
        role="user",
        parts=[StepStartUIPart()],  # Only step marker, no content
    )

    with pytest.raises(ValueError, match="No valid content blocks created"):
        _ui_message_to_domain_type(message)


def test_ui_request_to_domain_type():
    """Test conversion of full ChatRequest to domain messages."""
    request = ChatRequest(
        id="chat-1",
        messages=[
            UIMessage(
                id="msg-1",
                role="user",
                parts=[TextUIPart(text="Hello", state="done")],
            ),
            UIMessage(
                id="msg-2",
                role="assistant",
                parts=[TextUIPart(text="Hi there!", state="done")],
            ),
        ],
        trigger="submit-message",
    )

    result = ui_request_to_domain_type(request)

    assert len(result) == 2
    assert result[0].role.value == "user"
    assert result[0].blocks[0].content == "Hello"
    assert result[1].role.value == "assistant"
    assert result[1].blocks[0].content == "Hi there!"


def test_empty_request_raises_error():
    """Test that request with no messages raises error."""
    request = ChatRequest(id="chat-1", messages=[], trigger="submit-message")

    with pytest.raises(ValueError, match="No messages provided"):
        ui_request_to_domain_type(request)
