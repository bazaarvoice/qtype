### RAGChunk

A standard, built-in representation of a chunk of a document used in Retrieval-Augmented Generation (RAG).

- **chunk_id** (`str`): An unique identifier for the chunk.
- **document_id** (`str`): The identifier of the parent document.
- **vector** (`list[float] | None`): Optional vector embedding for the chunk.
