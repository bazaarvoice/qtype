### DocToTextConverter

Defines a step to convert raw documents (e.g., PDF, DOCX) loaded by a DocumentSource into plain text
using an external tool like Docling or LlamaParse for pre-processing before chunking.
The input and output are both RAGDocument, but the output after processing with have content of type markdown.

- **type** (`Literal`): (No documentation available.)
