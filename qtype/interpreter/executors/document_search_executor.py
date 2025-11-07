from typing import AsyncIterator

from qtype.dsl.domain_types import RAGChunk, RAGSearchResult
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import to_opensearch_client
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocumentSearch


class DocumentSearchExecutor(StepExecutor):
    """Executor for DocumentSearch steps using OpenSearch/Elasticsearch."""

    def __init__(
        self, step: DocumentSearch, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, DocumentSearch):
            raise ValueError(
                (
                    "DocumentSearchExecutor can only execute "
                    "DocumentSearch steps."
                )
            )
        self.step: DocumentSearch = step
        # Initialize the OpenSearch client once for the executor
        self.client = to_opensearch_client(
            self.step.index, self._secret_manager
        )
        self.index_name = self.step.index.name

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the DocumentSearch step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage with search results as RAGSearchResult instances.
        """
        input_id = self.step.inputs[0].id
        output_id = self.step.outputs[0].id

        try:
            # Get the search query text
            query_text = message.variables.get(input_id)
            if not isinstance(query_text, str):
                raise ValueError(
                    (
                        f"Input variable '{input_id}' must be a string "
                        f"(text query), got {type(query_text)}"
                    )
                )

            # Build the search query
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["content^2", "title", "*"],
                        "type": "best_fields",
                    }
                },
                "size": 10,  # Default top 10 results
            }

            # Apply any filters if specified
            if self.step.filters:
                if "query" in search_body:
                    search_body["query"] = {
                        "bool": {
                            "must": [search_body["query"]],
                            "filter": [
                                {"term": {k: v}}
                                for k, v in self.step.filters.items()
                            ],
                        }
                    }

            # Execute the search
            response = self.client.search(
                index=self.index_name, body=search_body
            )

            # Process each hit and yield as RAGSearchResult
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                doc_id = hit["_id"]
                score = hit["_score"]

                # Extract content (adjust field name based on your schema)
                content = source.get("content", "")

                # Build metadata from the source, excluding content field
                metadata = {
                    k: v for k, v in source.items() if k not in ["content"]
                }

                # Create a RAGChunk from the search result
                # Use the document ID as both chunk_id and document_id
                chunk = RAGChunk(
                    content=content,
                    chunk_id=doc_id,
                    document_id=source.get("document_id", doc_id),
                    vector=None,  # Document search doesn't return embeddings
                    metadata=metadata,
                )

                # Wrap in RAGSearchResult with the score
                search_result = RAGSearchResult(chunk=chunk, score=score)

                # Yield result for each document
                yield message.copy_with_variables({output_id: search_result})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
