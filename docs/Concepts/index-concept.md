# Index

An index represents a searchable data structure that enables retrieval operations within QType applications. Indexes provide the foundation for Retrieval Augmented Generation (RAG) patterns, semantic search, and knowledge retrieval workflows by allowing applications to search through large collections of documents, embeddings, or structured data.

Indexes abstract away the complexity of different search backends (vector databases, document stores, search engines) while providing a consistent interface for search operations. They can be configured with authentication, connection parameters, and search-specific settings to connect to external data sources.

## Rules and Behaviors

- **Unique IDs**: Each index must have a unique `id` within the application. Duplicate index IDs will result in a validation error.
- **Required Name**: The `name` field is mandatory and specifies the actual index, collection, or table name in the external system.
- **Abstract Base Class**: Index is an abstract base class - you must use concrete implementations like `VectorIndex` or `DocumentIndex`.
- **Authentication Support**: Indexes can reference an `AuthorizationProvider` for secure access to external search systems.
- **Flexible Configuration**: The `args` field allows index-specific configuration and connection parameters for different backends.
- **Reference by Search Steps**: Indexes are referenced by search steps like `VectorSearch` and `DocumentSearch` to perform queries.
- **Embedding Model Requirement**: `VectorIndex` requires an `embedding_model` to vectorize queries and match the embedding space of stored documents.

--8<-- "components/Index.md"

## Index Types

--8<-- "components/VectorIndex.md"

--8<-- "components/DocumentIndex.md"

## Related Concepts

Indexes are used by search [Steps](Steps/index.md) and require [Model](model.md) configurations (especially embedding models for vector indexes). They may also reference [AuthorizationProvider](authorization-provider.md) for secure access.

## Example Usage
