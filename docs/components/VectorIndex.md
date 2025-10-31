### VectorIndex

Vector database index for similarity search using embeddings.

- **type** (`Literal`): (No documentation available.)
- **module** (`str`): Module path of the LlamaIndex Index without 'llama_index.vector_stores' (e.g., 'qdrant.QdrantVectorStore', 'pinecone.PineconeVectorStore').
- **embedding_model** (`Reference[EmbeddingModel] | str`): Embedding model used to vectorize queries and documents.
