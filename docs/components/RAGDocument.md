### RAGDocument

A standard, built-in representation of a document used in Retrieval-Augmented Generation (RAG).

- **content** (`Any`): The main content of the document.
- **file_id** (`str`): An unique identifier for the file.
- **file_name** (`str`): The name of the file.
- **uri** (`str | None`): The URI where the document can be found.
- **metadata** (`dict[str, Any] | None`): Optional metadata associated with the document.
- **type** (`PrimitiveTypeEnum`): The type of the document content (e.g., 'text', 'image').
