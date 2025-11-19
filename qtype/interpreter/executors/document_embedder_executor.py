from typing import AsyncIterator

from botocore.exceptions import ClientError
from llama_index.core.base.embeddings.base import BaseEmbedding
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from qtype.dsl.domain_types import RAGChunk
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import to_embedding_model
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocumentEmbedder


def is_throttling_error(e):
    return (
        isinstance(e, ClientError)
        and e.response["Error"]["Code"] == "ThrottlingException"
    )


class DocumentEmbedderExecutor(StepExecutor):
    """Executor for DocumentEmbedder steps."""

    def __init__(
        self, step: DocumentEmbedder, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, DocumentEmbedder):
            raise ValueError(
                (
                    "DocumentEmbedderExecutor can only execute "
                    "DocumentEmbedder steps."
                )
            )
        self.step: DocumentEmbedder = step
        # Initialize the embedding model once for the executor
        self.embedding_model: BaseEmbedding = to_embedding_model(
            self.step.model
        )

    # TODO: properly abstract this into a mixin
    @retry(
        retry=retry_if_exception(is_throttling_error),
        wait=wait_exponential(multiplier=0.5, min=1, max=30),
        stop=stop_after_attempt(10),
    )
    async def _embed(self, text: str) -> list[float]:
        """Generate embedding for the given text using the embedding model.

        Args:
            text: The text to embed.
        Returns:
            The embedding vector as a list of floats.
        """
        return await self.embedding_model.aget_text_embedding(text=text)

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the DocumentEmbedder step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessage with embedded chunk.
        """
        input_id = self.step.inputs[0].id
        output_id = self.step.outputs[0].id

        try:
            # Get the input chunk
            chunk = message.variables.get(input_id)
            if not isinstance(chunk, RAGChunk):
                raise ValueError(
                    (
                        f"Input variable '{input_id}' must be a RAGChunk, "
                        f"got {type(chunk)}"
                    )
                )

            # Generate embedding for the chunk content
            vector = await self._embed(str(chunk.content))

            # Create the output chunk with the vector
            embedded_chunk = RAGChunk(
                vector=vector,
                content=chunk.content,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                metadata=chunk.metadata,
            )

            # Yield the result
            yield message.copy_with_variables({output_id: embedded_chunk})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
