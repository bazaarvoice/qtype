"""Vector search executor for retrieving relevant chunks from vector stores."""

from __future__ import annotations

import logging
from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import (
    from_node_with_score,
    to_llama_vector_store_and_retriever,
)
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import VectorIndex, VectorSearch

logger = logging.getLogger(__name__)


class VectorSearchExecutor(StepExecutor):
    """Executor for VectorSearch steps using LlamaIndex vector stores."""

    def __init__(
        self, step: VectorSearch, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, VectorSearch):
            raise ValueError(
                "VectorSearchExecutor can only execute VectorSearch steps."
            )
        self.step: VectorSearch = step

        if not isinstance(self.step.index, VectorIndex):
            raise ValueError(
                f"VectorSearch step {self.step.id} must reference a VectorIndex."
            )
        self.index: VectorIndex = self.step.index

        # Get the vector store and retriever
        self._vector_store, self._retriever = (
            to_llama_vector_store_and_retriever(
                self.step.index, self.context.secret_manager
            )
        )

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the VectorSearch step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage with search results.
        """
        try:
            # Get the query from the input variable
            # (validated to be exactly one text input)
            input_var = self.step.inputs[0]
            query = message.variables.get(input_var.id)

            if not isinstance(query, str):
                raise ValueError(
                    f"VectorSearch input must be text, got {type(query)}"
                )

            # Perform the vector search
            logger.debug(f"Performing vector search with query: {query}")
            nodes_with_scores = await self._retriever.aretrieve(query)

            # Convert results to RAGSearchResult objects
            search_results = [
                from_node_with_score(node_with_score)
                for node_with_score in nodes_with_scores
            ]

            # Set the output variable (validated to be exactly one output
            # of type list[RAGSearchResult])
            output_var = self.step.outputs[0]
            output_vars = {output_var.id: search_results}

            yield message.copy_with_variables(output_vars)

        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
