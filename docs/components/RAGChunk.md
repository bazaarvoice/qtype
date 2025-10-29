### RAGChunk

A standard, built-in representation of a chunk of a document used in Retrieval-Augmented Generation (RAG).

- **content** (`str`): The text content of the chunk.
- **chunk_id** (`str`): An unique identifier for the chunk.
- **document_id** (`str`): The identifier of the parent document.
- **embedding** (`Embedding | None`): Optional embedding associated with the chunk.
- **metadata** (`dict[str, Any] | None`): Optional metadata associated with the chunk.
