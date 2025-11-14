# Index

An index represents a searchable data structure that enables retrieval operations within QType applications. Indexes provide the foundation for Retrieval Augmented Generation (RAG) patterns, semantic search, and knowledge retrieval workflows by allowing applications to search through large collections of documents, embeddings, or structured data.

Indexes are defined at the application level and referenced by search steps that need to query data.

## Key Principles

### Type Discriminator

All indexes must include a `type` field for proper schema validation:
- `type: VectorIndex` for vector/embedding similarity search
- `type: DocumentIndex` for text-based document search

### Centralized Definition & Reference by ID

Indexes are defined at the application level and referenced by ID:

```yaml
indexes:
  - type: VectorIndex
    id: my_vector_db
    name: embeddings_collection
    embedding_model: text_embedder
    args:
      host: localhost
      port: 6333

flows:
  - type: Flow
    id: search_flow
    steps:
      - type: VectorSearch
        index: my_vector_db  # References by ID
```

## Rules and Behaviors

- **Unique IDs**: Each index must have a unique `id` within the application. Duplicate index IDs will result in a validation error.
- **Required Name**: The `name` field specifies the actual index, collection, or table name in the external system.
- **Authentication Support**: Indexes can reference an `AuthorizationProvider` by ID for secure access to external search systems.
- **Flexible Configuration**: The `args` field allows index-specific configuration and connection parameters for different backends.
- **Embedding Model Requirement**: `VectorIndex` requires an `embedding_model` reference to vectorize queries and match the embedding space of stored documents.

--8<-- "components/Index.md"

## Index Types

--8<-- "components/VectorIndex.md"

--8<-- "components/DocumentIndex.md"

## Related Concepts

Indexes are used by search [Steps](../Steps/index.md) and require [Model](model.md) configurations (especially embedding models for vector indexes). They may also reference [AuthorizationProvider](authorization-provider.md) for secure access.

## Example Usage
