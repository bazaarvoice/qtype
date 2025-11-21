### RAGSearchResult

A standard, built-in representation of a search result from a RAG vector search.
Note: doc_id is duplicated from content.document_id for convenience.

- **content** (`RAGChunk`): The RAG chunk returned as a search result.
- **doc_id** (`str`): The document ID (duplicated from content.document_id).
- **score** (`float`): The similarity score of the chunk with respect to the query.
