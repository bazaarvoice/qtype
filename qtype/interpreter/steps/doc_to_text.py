from io import BytesIO

from docling.document_converter import DocumentConverter
from docling_core.types.io import DocumentStream

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.domain_types import RAGDocument
from qtype.semantic.model import DocToTextConverter, Variable


def _doc_to_text(
    doc: RAGDocument, converter: DocumentConverter
) -> RAGDocument:
    if doc.type == PrimitiveTypeEnum.text:
        return doc  # No conversion needed

    # converter.convert takes a Union[Path, str, DocumentStream]
    # RAGDocument.content is str | bytes
    document = converter.convert(doc.content).document
    markdown = document.export_to_markdown()
    if isinstance(doc.content, bytes):
        stream = DocumentStream(
            name=doc.file_name, stream=BytesIO(doc.content)
        )
        document = converter.convert(stream).document
    else:
        document = converter.convert(doc.content).document

    return RAGDocument(
        **doc.model_dump(),
        content=markdown,
        type=PrimitiveTypeEnum.text,
    )


def execute_doc_to_text(
    converter: DocToTextConverter,
) -> list[Variable]:
    """Execute a DocToTextConverter step to convert documents to text.

    Args:
        converter: The DocToTextConverter step to execute.
        docs: List of RAGDocument instances to convert.

    Returns:
        A list of converted RAGDocument instances.
    """
    docling_converter = DocumentConverter()

    if len(converter.inputs) != 1:
        raise ValueError(
            "DocToTextConverter step must have exactly one input variable."
        )
    if len(converter.outputs) != 1:
        raise ValueError(
            "DocToTextConverter step must have exactly one output variable."
        )

    converted_doc = _doc_to_text(converter.inputs[0].value, docling_converter)  # type: ignore

    converter.outputs[0].value = converted_doc

    return converter.outputs
