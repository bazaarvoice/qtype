from __future__ import annotations

import logging
from typing import Any

from qtype.dsl.domain_types import Embedding, RAGChunk
from qtype.interpreter.conversions import to_embedding_model
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import DocumentEmbedder, Variable

logger = logging.getLogger(__name__)


def execute(
    embedder: DocumentEmbedder,
    **kwargs: dict[Any, Any],
) -> list[Variable]:
    """Execute a DocumentEmbedder step to embed document chunks.

    Args:
        embedder: The DocumentEmbedder step to execute.
        **kwargs: Additional keyword arguments.

    Returns:
        A list containing the output variable with the embedded chunk.
    """
    logger.debug(f"Executing DocumentEmbedder step: {embedder.id}")

    # Validate inputs and outputs
    if len(embedder.inputs) != 1:
        raise InterpreterError(
            "DocumentEmbedder step must have exactly one input variable."
        )
    if len(embedder.outputs) != 1:
        raise InterpreterError(
            "DocumentEmbedder step must have exactly one output variable."
        )

    input_variable = embedder.inputs[0]
    output_variable = embedder.outputs[0]

    # Get the input chunk
    chunk = input_variable.value
    if not isinstance(chunk, RAGChunk):
        raise InterpreterError(
            f"DocumentEmbedder input must be a RAGChunk, got {type(chunk)}"
        )

    # Get the embedding model
    embedding_model = to_embedding_model(embedder.model)

    # Generate embedding for the chunk content
    vector = embedding_model.get_text_embedding(text=chunk.content)

    # Create an Embedding object
    embedding = Embedding(
        vector=vector,
        source_text=chunk.content,
        metadata=chunk.metadata,
    )

    # Create the output chunk with the embedding
    embedded_chunk = RAGChunk(
        content=chunk.content,
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        embedding=embedding,
        metadata=chunk.metadata,
    )

    # Set the output variable
    output_variable.value = embedded_chunk

    return embedder.outputs  # type: ignore[return-value]
