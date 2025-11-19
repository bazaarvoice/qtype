from typing import AsyncIterator

from openinference.semconv.trace import OpenInferenceSpanKindValues

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import Embedding
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import to_embedding_model
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import InvokeEmbedding


class InvokeEmbeddingExecutor(StepExecutor):
    """Executor for InvokeEmbedding steps."""

    # Embedding operations should be marked as EMBEDDING type
    span_kind = OpenInferenceSpanKindValues.EMBEDDING

    def __init__(
        self, step: InvokeEmbedding, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, InvokeEmbedding):
            raise ValueError(
                (
                    "InvokeEmbeddingExecutor can only execute "
                    "InvokeEmbedding steps."
                )
            )
        self.step: InvokeEmbedding = step
        # Initialize the embedding model once for the executor
        self.embedding_model = to_embedding_model(self.step.model)

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the InvokeEmbedding step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessage with embedding.
        """
        input_id = self.step.inputs[0].id
        input_type = self.step.inputs[0].type
        output_id = self.step.outputs[0].id

        try:
            # Get the input value
            input_value = message.variables.get(input_id)

            if input_value is None:
                raise ValueError(f"Input variable '{input_id}' is missing")

            # Generate embedding based on input type
            if input_type == PrimitiveTypeEnum.text:
                if not isinstance(input_value, str):
                    input_value = str(input_value)
                vector = await self.embedding_model.aget_text_embedding(
                    text=input_value
                )
                content = input_value
            elif input_type == PrimitiveTypeEnum.image:
                # For image embeddings
                vector = await self.embedding_model.aget_image_embedding(
                    image_path=input_value
                )
                content = input_value
            else:
                raise ValueError(
                    (
                        f"Unsupported input type for embedding: "
                        f"{input_type}. Must be 'text' or 'image'."
                    )
                )

            # Create the Embedding object
            embedding = Embedding(
                vector=vector,
                content=content,
            )

            # Yield the result
            yield message.copy_with_variables({output_id: embedding})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
