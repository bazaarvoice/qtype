"""
Unit tests for QType semantic validation - Section 4: Memory vs Retriever.

This module tests memory vs retriever usage validation rules as defined in
semantic_ir.md Section 4.
"""

import unittest

from qtype.dsl.model import (
    EmbeddingModel,
    Flow,
    FlowMode,
    Memory,
    MemoryType,
    QTypeSpec,
    Step,
    VectorDBRetriever,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class MemoryUsageTest(unittest.TestCase):
    """Test Section 4: Memory vs Retriever usage validation rules."""

    def test_memory_not_used_as_step_component_success(self) -> None:
        """Test that memory IDs are correctly used in flow.memory, not as step components."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="chat_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                )
            ],
            retrievers=[
                VectorDBRetriever(
                    id="doc_retriever",
                    index="docs",
                    embedding_model="embed_model",
                )
            ],
            flows=[
                Flow(
                    id="chat_flow",
                    mode=FlowMode.chat,
                    memory=["chat_memory"],
                    steps=[
                        Step(
                            id="step1",
                            component="doc_retriever",
                            output_vars=["retrieved_docs"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_memory_used_as_step_component_failure(self) -> None:
        """Test that using memory ID as step component fails validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="chat_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                )
            ],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="chat_memory",  # Invalid: memory as component
                            output_vars=["result"],
                        )
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Memory 'chat_memory' cannot be used as a Step component",
            str(context.exception),
        )
        self.assertIn("Use retrievers for step-level operations", str(context.exception))

    def test_retriever_used_as_step_component_success(self) -> None:
        """Test that retrievers can be used as step components."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            retrievers=[
                VectorDBRetriever(
                    id="doc_retriever",
                    index="docs",
                    embedding_model="embed_model",
                )
            ],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="doc_retriever",
                            output_vars=["retrieved_docs"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_memory_and_retriever_can_share_embedding_model_success(self) -> None:
        """Test that memory and retrievers can share the same embedding model."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="shared_embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="chat_memory",
                    type=MemoryType.vector,
                    embedding_model="shared_embed_model",
                )
            ],
            retrievers=[
                VectorDBRetriever(
                    id="doc_retriever",
                    index="docs",
                    embedding_model="shared_embed_model",
                )
            ],
            flows=[
                Flow(
                    id="chat_flow",
                    mode=FlowMode.chat,
                    memory=["chat_memory"],
                    steps=[
                        Step(
                            id="step1",
                            component="doc_retriever",
                            output_vars=["retrieved_docs"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_memory_only_used_in_flow_memory_field_success(self) -> None:
        """Test that memory components are only referenced in flow.memory field."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="session_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                ),
                Memory(
                    id="persistent_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                    persist=True,
                ),
            ],
            flows=[
                Flow(
                    id="chat_flow",
                    mode=FlowMode.chat,
                    memory=["session_memory", "persistent_memory"],
                    steps=[],
                )
            ],
        )
        validate_semantics(spec)


if __name__ == "__main__":
    unittest.main()
