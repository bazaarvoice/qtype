"""BedrockReranker executor for reordering search results by relevance."""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from pydantic import BaseModel

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import RAGChunk, SearchResult
from qtype.interpreter.auth.aws import aws
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import BedrockReranker, ListType

logger = logging.getLogger(__name__)


class BedrockRerankerExecutor(StepExecutor):
    """Executor for BedrockReranker steps that reorder search results by relevance."""

    def __init__(
        self, step: BedrockReranker, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, BedrockReranker):
            raise ValueError(
                "BedrockRerankerExecutor can only execute BedrockReranker steps."
            )
        self.step: BedrockReranker = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the BedrockReranker step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage with reranked results.
        """
        try:
            # Get the inputs
            query = self._query(message)
            docs = self._docs(message)

            if len(docs) == 0:
                # No documents to rerank, yield original message
                yield message.copy_with_variables(
                    {self.step.outputs[0].id: docs}
                )
                return

            # Get session for region info
            if self.step.auth is not None:
                with aws(self.step.auth, self.context.secret_manager) as s:
                    region_name = s.region_name
            else:
                import boto3

                region_name = boto3.Session().region_name

            # Convert the types
            queries = [
                {
                    "type": "TEXT",
                    "textQuery": {"text": query},
                }
            ]
            documents = []

            for doc in docs:
                if isinstance(doc.content, RAGChunk):
                    documents.append(
                        {
                            "type": "INLINE",
                            "inlineDocumentSource": {
                                "type": "TEXT",
                                "textDocument": {"text": str(doc.content)},
                            },
                        }
                    )
                elif isinstance(doc.content, dict):
                    documents.append(
                        {
                            "type": "INLINE",
                            "inlineDocumentSource": {
                                "type": "JSON",
                                "jsonDocument": doc.content,
                            },
                        }
                    )
                elif isinstance(doc.content, BaseModel):
                    documents.append(
                        {
                            "type": "INLINE",
                            "inlineDocumentSource": {
                                "type": "JSON",
                                "jsonDocument": doc.content.model_dump(),
                            },
                        }
                    )
                else:
                    raise ValueError(
                        f"Unsupported document content type for BedrockReranker: {type(doc.content)}"
                    )

            reranking_configuration = {
                "type": "BEDROCK_RERANKING_MODEL",
                "bedrockRerankingConfiguration": {
                    "numberOfResults": self.step.num_results or len(docs),
                    "modelConfiguration": {
                        "modelArn": f"arn:aws:bedrock:{region_name}::foundation-model/{self.step.model_id}"
                    },
                },
            }

            def _call_bedrock_rerank():
                """Create client and call rerank in executor thread."""
                if self.step.auth is not None:
                    with aws(self.step.auth, self.context.secret_manager) as s:
                        client = s.client("bedrock-agent-runtime")
                        return client.rerank(
                            queries=queries,
                            sources=documents,
                            rerankingConfiguration=reranking_configuration,
                        )
                else:
                    import boto3

                    session = boto3.Session()
                    client = session.client("bedrock-agent-runtime")
                    return client.rerank(
                        queries=queries,
                        sources=documents,
                        rerankingConfiguration=reranking_configuration,
                    )

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                self.context.thread_pool, _call_bedrock_rerank
            )

            results = []
            for d in response["results"]:
                doc = docs[d["index"]]
                new_score = d["relevanceScore"]
                results.append(doc.copy(update={"score": new_score}))

            # Update the message with reranked results
            yield message.copy_with_variables(
                {self.step.outputs[0].id: results}
            )
        except Exception as e:
            logger.error(f"Reranking failed: {e}", exc_info=True)
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            yield message.copy_with_error(self.step.id, e)

    def _query(self, message: FlowMessage) -> str:
        """Extract the query string from the FlowMessage.

        Args:
            message: The FlowMessage containing the query variable.
        Returns:
            The query string.
        """
        for i in self.step.inputs:
            if i.type == PrimitiveTypeEnum.text:
                return message.variables[i.id]
        raise ValueError(
            f"No text input found for BedrockReranker step {self.step.id}"
        )

    def _docs(self, message: FlowMessage) -> list[SearchResult]:
        """Extract the list of SearchResult documents from the FlowMessage.

        Args:
            message: The FlowMessage containing the document variable.
        Returns:
            The list of SearchResult documents.
        """
        for i in self.step.inputs:
            if i.type == ListType(element_type="SearchResult"):
                docs = message.variables[i.id]
                return docs
        raise ValueError(
            f"No list of SearchResults input found for BedrockReranker step {self.step.id}"
        )
