from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from qtype.dsl.domain_types import SearchResult
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

    async def _search_opensearch(
        self, search_body: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute OpenSearch search in a thread pool.

        Args:
            search_body: OpenSearch query body

        Returns:
            OpenSearch search response
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.client.search(
                index=self.index_name, body=search_body
            ),
        )

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the DocumentSearch step.

        Args:
            message: The FlowMessage to process.

        Yields:
            A list of dictionaries with _source, _search_score, and _search_id fields.
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
                    "multi_match": {"query": query_text} | self.step.query_args
                },
                "size": self.step.default_top_k,
            }

            # Apply any filters if specified
            if self.step.filters:
                search_body["query"] = {
                    "bool": {
                        "must": [search_body["query"]],
                        "filter": [
                            {"term": {k: v}}
                            for k, v in self.step.filters.items()
                        ],
                    }
                }

            # Execute the search asynchronously
            response = await self._search_opensearch(search_body)

            # Process each hit and yield as SearchResult
            # TODO: add support for decomposing a RAGSearchResult for hybrid search
            search_results = []
            for hit in response["hits"]["hits"]:
                doc = hit["_source"].copy()
                doc["_search_score"] = hit["_score"]
                doc["_search_id"] = hit["_id"]
                search_results.append(SearchResult(**doc))
            yield message.copy_with_variables({output_id: search_results})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
