from typing import AsyncIterator

from llama_index.core.schema import Document as LlamaDocument

from qtype.dsl.domain_types import RAGChunk, RAGDocument
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import to_text_splitter
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocumentSplitter


class DocumentSplitterExecutor(StepExecutor):
    """Executor for DocumentSplitter steps."""

    def __init__(
        self, step: DocumentSplitter, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, DocumentSplitter):
            raise ValueError(
                (
                    "DocumentSplitterExecutor can only execute "
                    "DocumentSplitter steps."
                )
            )
        self.step: DocumentSplitter = step
        # Initialize the text splitter once for the executor
        self.llama_splitter = to_text_splitter(self.step)

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the DocumentSplitter step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessages with document chunks.
        """
        input_id = self.step.inputs[0].id
        output_id = self.step.outputs[0].id

        try:
            # Get the document from the input
            document = message.variables.get(input_id)
            if not isinstance(document, RAGDocument):
                raise ValueError(
                    f"Input variable '{input_id}' must be a RAGDocument"
                )

            await self.stream_emitter.status(
                f"Splitting document: {document.file_name}"
            )

            # Convert content to text if needed
            if isinstance(document.content, bytes):
                content_text = document.content.decode("utf-8")
            elif isinstance(document.content, str):
                content_text = document.content
            else:
                raise ValueError(
                    (
                        f"Unsupported document content type: "
                        f"{type(document.content)}"
                    )
                )

            # Convert to LlamaIndex Document for splitting
            llama_doc = LlamaDocument(
                text=content_text,
                metadata=document.metadata or {},
                doc_id=document.file_id,
            )

            # Split the document using the LlamaIndex splitter
            nodes = self.llama_splitter.get_nodes_from_documents([llama_doc])

            await self.stream_emitter.status(
                f"Split {document.file_name} into {len(nodes)} chunks"
            )

            # Create a RAGChunk for each node and yield (fan-out)
            for node in nodes:
                merged_metadata = {}
                merged_metadata.update(document.metadata)
                if node.metadata:
                    merged_metadata.update(node.metadata)

                chunk = RAGChunk(
                    content=node.text,
                    chunk_id=node.node_id,
                    document_id=document.file_id,
                    vector=None,  # Embedding will be added later
                    metadata=merged_metadata,
                )
                yield message.copy_with_variables({output_id: chunk})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
