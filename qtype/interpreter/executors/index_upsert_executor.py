"""Index upsert executor for inserting documents/chunks into indexes."""

from __future__ import annotations

import logging
from typing import AsyncIterator

from llama_index.core.schema import TextNode

from qtype.dsl.domain_types import RAGChunk, RAGDocument
from qtype.interpreter.base.batch_step_executor import BatchedStepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import (
    to_llama_vector_store_and_retriever,
    to_opensearch_client,
)
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocumentIndex, IndexUpsert, VectorIndex

logger = logging.getLogger(__name__)


class IndexUpsertExecutor(BatchedStepExecutor):
    """Executor for IndexUpsert steps supporting both vector and document indexes."""

    def __init__(
        self, step: IndexUpsert, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, IndexUpsert):
            raise ValueError(
                "IndexUpsertExecutor can only execute IndexUpsert steps."
            )
        self.step: IndexUpsert = step

        # Determine index type and initialize appropriate client
        if isinstance(self.step.index, VectorIndex):
            # Vector index for RAGChunk embeddings
            self._vector_store, _ = to_llama_vector_store_and_retriever(
                self.step.index, self.context.secret_manager
            )
            self._opensearch_client = None
            self.index_type = "vector"
        elif isinstance(self.step.index, DocumentIndex):
            # Document index for text-based search
            self._opensearch_client = to_opensearch_client(
                self.step.index, self.context.secret_manager
            )
            self._vector_store = None
            self.index_type = "document"
            self.index_name = self.step.index.name
        else:
            raise ValueError(
                f"Unsupported index type: {type(self.step.index)}"
            )

    async def process_batch(
        self, batch: list[FlowMessage]
    ) -> AsyncIterator[FlowMessage]:
        """Process a batch of FlowMessages for the IndexUpsert step.

        Args:
            batch: A list of FlowMessages to process.

        Yields:
            FlowMessages: Success messages after upserting to the index
        """
        logger.debug(
            f"Executing IndexUpsert step: {self.step.id} with batch size: {len(batch)}"
        )

        try:
            # Get the input variable (exactly one as validated by checker)
            if not self.step.inputs:
                raise ValueError("IndexUpsert step requires exactly one input")

            input_var = self.step.inputs[0]

            # Collect all RAGChunks or RAGDocuments from the batch
            items_to_upsert = []
            for message in batch:
                input_data = message.variables.get(input_var.id)

                if input_data is None:
                    logger.warning(
                        f"No data found for input: {input_var.id} in message"
                    )
                    continue

                if not isinstance(input_data, (RAGChunk, RAGDocument)):
                    raise ValueError(
                        f"IndexUpsert only supports RAGChunk or RAGDocument "
                        f"inputs. Got: {type(input_data)}"
                    )

                items_to_upsert.append(input_data)

            # Upsert to appropriate index type
            if items_to_upsert:
                if self.index_type == "vector":
                    await self._upsert_to_vector_store(items_to_upsert)
                else:  # document index
                    await self._upsert_to_document_index(items_to_upsert)

                logger.debug(
                    f"Successfully upserted {len(items_to_upsert)} items "
                    f"to {self.index_type} index in batch"
                )

                # Emit status update
                index_type_display = (
                    "vector index"
                    if self.index_type == "vector"
                    else "document index"
                )
                await self.stream_emitter.status(
                    f"Upserted {len(items_to_upsert)} items to "
                    f"{index_type_display}"
                )

            # Yield all input messages back (IndexUpsert typically doesn't have outputs)
            for message in batch:
                yield message

        except Exception as e:
            logger.error(f"Error in IndexUpsert step {self.step.id}: {e}")
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))

            # Mark all messages with the error and yield them
            for message in batch:
                message.set_error(self.step.id, e)
                yield message

    async def _upsert_to_vector_store(
        self, items: list[RAGChunk | RAGDocument]
    ) -> None:
        """Upsert items to vector store.

        Args:
            items: List of RAGChunk or RAGDocument objects
        """
        # Convert to LlamaIndex TextNode objects
        nodes = []
        for item in items:
            if isinstance(item, RAGChunk):
                node = TextNode(
                    id_=item.chunk_id,
                    text=str(item.content),
                    metadata=item.metadata,
                    embedding=item.vector,
                )
            else:  # RAGDocument
                # For documents, use file_id and convert content to string
                node = TextNode(
                    id_=item.file_id,
                    text=str(item.content),
                    metadata=item.metadata,
                    embedding=None,  # Documents don't have embeddings
                )
            nodes.append(node)

        # Batch upsert all nodes to the vector store
        await self._vector_store.async_add(nodes)

    async def _upsert_to_document_index(
        self, items: list[RAGChunk | RAGDocument]
    ) -> None:
        """Upsert items to document index using bulk API.

        Args:
            items: List of RAGChunk or RAGDocument objects
        """
        # Build bulk request body
        bulk_body = []
        for item in items:
            if isinstance(item, RAGChunk):
                # Add index action
                bulk_body.append(
                    {
                        "index": {
                            "_index": self.index_name,
                            "_id": item.chunk_id,
                        }
                    }
                )
                # Add document content
                doc = {
                    "text": str(item.content),
                    "metadata": item.metadata,
                }
                # Include embedding if available
                if item.vector:
                    doc["embedding"] = item.vector
                bulk_body.append(doc)
            else:  # RAGDocument
                # Add index action
                bulk_body.append(
                    {
                        "index": {
                            "_index": self.index_name,
                            "_id": item.file_id,
                        }
                    }
                )
                # Add document content
                doc = {
                    "text": str(item.content),
                    "metadata": item.metadata,
                    "file_name": item.file_name,
                }
                if item.uri:
                    doc["uri"] = item.uri
                bulk_body.append(doc)

        # Execute bulk request
        response = self._opensearch_client.bulk(body=bulk_body)

        # Check for errors
        if response.get("errors"):
            error_items = [
                item
                for item in response["items"]
                if "error" in item.get("index", {})
            ]
            logger.warning(
                f"Bulk upsert had {len(error_items)} errors: {error_items}"
            )
