from io import BytesIO
from typing import AsyncIterator

from docling.document_converter import DocumentConverter
from docling_core.types.io import DocumentStream

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import RAGDocument
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocToTextConverter


class DocToTextConverterExecutor(StepExecutor):
    """Executor for DocToTextConverter steps."""

    def __init__(
        self,
        step: DocToTextConverter,
        context: ExecutorContext,
        **dependencies,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, DocToTextConverter):
            raise ValueError(
                (
                    "DocToTextConverterExecutor can only execute "
                    "DocToTextConverter steps."
                )
            )
        self.step: DocToTextConverter = step
        # Initialize the Docling converter once for the executor
        self.docling_converter = DocumentConverter()

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the DocToTextConverter step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessage with converted document.
        """
        input_id = self.step.inputs[0].id
        output_id = self.step.outputs[0].id

        try:
            # Get the input document
            if input_id not in message.variables:
                raise ValueError(f"Input variable '{input_id}' is missing")
            doc = message.variables.get(input_id)
            if not isinstance(doc, RAGDocument):
                raise ValueError(
                    f"Input variable '{input_id}' must be a RAGDocument"
                )

            await self.stream_emitter.status(
                f"Converting document: {doc.file_name}",
            )

            # Convert the document
            converted_doc = self._convert_doc(doc)

            await self.stream_emitter.status(
                f"Converted {doc.file_name} to markdown text",
            )

            # Yield the result
            yield message.copy_with_variables({output_id: converted_doc})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message

    def _convert_doc(self, doc: RAGDocument) -> RAGDocument:
        """Convert a RAGDocument to text/markdown format.

        Args:
            doc: The document to convert.

        Returns:
            A RAGDocument with markdown text content.
        """
        # If already text, no conversion needed
        if doc.type == PrimitiveTypeEnum.text:
            return doc

        # Convert based on content type
        if isinstance(doc.content, bytes):
            # Use DocumentStream for bytes content
            stream = DocumentStream(
                name=doc.file_name, stream=BytesIO(doc.content)
            )
            document = self.docling_converter.convert(stream).document
        else:
            # Convert string content directly
            document = self.docling_converter.convert(doc.content).document

        # Export to markdown
        markdown = document.export_to_markdown()

        # Return new RAGDocument with markdown content
        return RAGDocument(
            **doc.model_dump(exclude={"content", "type"}),
            content=markdown,
            type=PrimitiveTypeEnum.text,
        )
