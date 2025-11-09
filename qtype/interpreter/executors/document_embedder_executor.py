from typing import AsyncIterator

from qtype.dsl.domain_types import RAGChunk
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import to_embedding_model
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocumentEmbedder


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
        self.embedding_model = to_embedding_model(self.step.model)

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
            vector = self.embedding_model.get_text_embedding(
                text=str(chunk.content)
            )

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
