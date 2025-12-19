"""Index upsert executor for inserting documents/chunks into indexes."""

from __future__ import annotations

import logging
import uuid
from typing import AsyncIterator

from llama_index.core.schema import TextNode
from opensearchpy import AsyncOpenSearch
from pydantic import BaseModel

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
            self.index_type = "vector"
        elif isinstance(self.step.index, DocumentIndex):
            # Document index for text-based search
            self._opensearch_client: AsyncOpenSearch = to_opensearch_client(
                self.step.index, self.context.secret_manager
            )
            self._vector_store = None
            self.index_type = "document"
            self.index_name = self.step.index.name
            self._document_index: DocumentIndex = self.step.index
        else:
            raise ValueError(
                f"Unsupported index type: {type(self.step.index)}"
            )

    async def finalize(self) -> AsyncIterator[FlowMessage]:
        """Clean up resources after all messages are processed."""
        if hasattr(self, "_opensearch_client") and self._opensearch_client:
            try:
                await self._opensearch_client.close()
            except Exception:
                pass
        # Make this an async generator
        return
        yield  # type: ignore[unreachable]

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
        if len(batch) == 0:
            return

        try:
            if self.index_type == "vector":
                result_iter = self._upsert_to_vector_store(batch)
            else:
                result_iter = self._upsert_to_document_index(batch)
            async for message in result_iter:
                yield message

        except Exception as e:
            logger.error(f"Error in IndexUpsert step {self.step.id}: {e}")
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))

            # Mark all messages with the error and yield them
            for message in batch:
                yield message.copy_with_error(self.step.id, e)

    async def _upsert_to_vector_store(
        self, batch: list[FlowMessage]
    ) -> AsyncIterator[FlowMessage]:
        """Upsert items to vector store.

        Args:
            items: List of RAGChunk or RAGDocument objects
        """
        # safe since semantic validation checks input length
        input_var = self.step.inputs[0]

        # Collect all RAGChunks or RAGDocuments from the batch inputs
        items = []
        for message in batch:
            input_data = message.variables.get(input_var.id)
            if not isinstance(input_data, (RAGChunk, RAGDocument)):
                raise ValueError(
                    f"IndexUpsert only supports RAGChunk or RAGDocument "
                    f"inputs. Got: {type(input_data)}"
                )
            items.append(input_data)

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
        num_inserted = len(items)

        # Emit status update
        await self.stream_emitter.status(
            f"Upserted {num_inserted} items to index {self.step.index.name}"
        )
        for message in batch:
            yield message

    async def _upsert_to_document_index(
        self, batch: list[FlowMessage]
    ) -> AsyncIterator[FlowMessage]:
        """Upsert items to document index using bulk API.

        Args:
            batch: List of FlowMessages containing documents to upsert
        """

        bulk_body = []
        message_by_id: dict[str, FlowMessage] = {}

        for message in batch:
            # Collect all input variables into a single document dict
            doc_dict = {}
            for input_var in self.step.inputs:
                value = message.variables.get(input_var.id)

                # Convert to dict if it's a Pydantic model
                if isinstance(value, BaseModel):
                    value = value.model_dump()

                # Merge into document dict
                if isinstance(value, dict):
                    doc_dict.update(value)
                else:
                    # Primitive types - use variable name as field name
                    doc_dict[input_var.id] = value

            # Determine the document id field
            id_field = None
            if self._document_index.id_field is not None:
                id_field = self._document_index.id_field
                if id_field not in doc_dict:
                    raise ValueError(
                        f"Specified id_field '{id_field}' not found in inputs"
                    )
            else:
                # Auto-detect with fallback
                for field in ["_id", "id", "doc_id", "document_id"]:
                    if field in doc_dict:
                        id_field = field
                        break
            if id_field is not None:
                doc_id = str(doc_dict[id_field])
            else:
                # Generate a UUID if no id field found
                doc_id = str(uuid.uuid4())

            # Add bulk action and document
            bulk_body.append(
                {"index": {"_index": self.index_name, "_id": doc_id}}
            )
            bulk_body.append(doc_dict)
            message_by_id[doc_id] = message

        # Execute bulk request asynchronously
        response = await self._opensearch_client.bulk(body=bulk_body)

        num_inserted = 0
        for item in response["items"]:
            doc_id = item["index"]["_id"]
            message = message_by_id[doc_id]
            if "error" in item.get("index", {}):
                yield message.copy_with_error(
                    self.step.id,
                    Exception(item["index"]["error"]),
                )
            else:
                num_inserted += 1
                yield message
        await self.stream_emitter.status(
            f"Upserted {num_inserted} items to index {self.step.index.name}, {len(batch) - num_inserted} errors occurred."
        )
