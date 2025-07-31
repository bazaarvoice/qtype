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

Indexes are used by search [Steps](step.md) and require [Model](model.md) configurations (especially embedding models for vector indexes). They may also reference [AuthorizationProvider](authorization-provider.md) for secure access.

## Example Usage

### Vector Index for Semantic Search

```yaml
id: knowledge_base_app

models:
  - id: text_embeddings
    provider: openai
    model_id: text-embedding-3-small
    dimensions: 1536
    auth: openai_auth

auths:
  - id: openai_auth
    type: api_key
    api_key: ${OPENAI_API_KEY}
  
  - id: pinecone_auth
    type: api_key
    api_key: ${PINECONE_API_KEY}

indexes:
  - id: document_vectors
    name: knowledge-base
    embedding_model: text_embeddings
    auth: pinecone_auth
    args:
      host: https://knowledge-base-abc123.svc.us-east1-gcp.pinecone.io
      dimension: 1536
      metric: cosine

flows:
  - id: semantic_search_flow
    steps:
      - id: find_relevant_docs
        index: document_vectors
        inputs:
          - id: search_query
            type: text
          - id: top_k
            type: number
        outputs:
          - id: search_results
            type: text
```

### Document Index for Full-Text Search

```yaml
auths:
  - id: elasticsearch_auth
    type: api_key
    api_key: ${ELASTICSEARCH_API_KEY}
    host: https://my-deployment.es.us-central1.gcp.cloud.es.io

indexes:
  - id: document_store
    name: documents
    auth: elasticsearch_auth
    args:
      index_name: company_documents
      connection_timeout: 30
      max_retries: 3

flows:
  - id: document_search_flow
    steps:
      - id: search_documents
        index: document_store
        filters:
          category: "policy"
          date_range:
            from: "2024-01-01"
            to: "2024-12-31"
        inputs:
          - id: search_terms
            type: text
        outputs:
          - id: matching_documents
            type: text
```

### Multi-Index RAG Pipeline

```yaml
models:
  - id: embedding_model
    provider: openai
    model_id: text-embedding-3-large
    dimensions: 3072
  
  - id: chat_model
    provider: openai
    model_id: gpt-4o
    auth: openai_auth

indexes:
  - id: technical_docs
    name: technical-documentation
    embedding_model: embedding_model
    auth: pinecone_auth
    args:
      namespace: "technical"
  
  - id: policy_docs
    name: policy-documents
    auth: elasticsearch_auth
    args:
      index_name: "policies"

flows:
  - id: comprehensive_search
    steps:
      - id: search_technical
        index: technical_docs
        inputs:
          - id: query
            type: text
        outputs:
          - id: technical_results
            type: text
      
      - id: search_policies
        index: policy_docs
        inputs:
          - id: query
            type: text
        outputs:
          - id: policy_results
            type: text
      
      - id: synthesize_answer
        model: chat_model
        system_message: |
          You are a helpful assistant. Use the provided technical documentation 
          and policy information to answer the user's question comprehensively.
        inputs:
          - id: user_question
            type: text
          - id: technical_context
            type: text
          - id: policy_context
            type: text
        outputs:
          - id: comprehensive_answer
            type: text
```

### Embedded Index Configuration

```yaml
flows:
  - id: quick_search_flow
    steps:
      - id: embedded_search
        index:
          id: temp_vector_index
          name: temporary-vectors
          embedding_model: 
            id: quick_embeddings
            provider: openai
            model_id: text-embedding-3-small
            dimensions: 1536
          auth:
            id: temp_auth
            type: api_key
            api_key: ${VECTOR_DB_KEY}
          args:
            host: ${VECTOR_DB_HOST}
            dimension: 1536
        inputs:
          - id: search_text
            type: text
        outputs:
          - id: results
            type: text
```

### Cross-Platform Index Integration

```yaml
auths:
  - id: weaviate_auth
    type: api_key
    api_key: ${WEAVIATE_API_KEY}
    host: https://my-cluster.weaviate.network
  
  - id: opensearch_auth
    type: api_key
    api_key: ${OPENSEARCH_API_KEY}
    host: https://search-domain.us-east-1.es.amazonaws.com

indexes:
  - id: vector_knowledge
    name: KnowledgeBase
    embedding_model: text_embeddings
    auth: weaviate_auth
    args:
      class_name: "Document"
      properties: ["content", "title", "category"]
  
  - id: structured_data
    name: structured_index
    auth: opensearch_auth
    args:
      index_pattern: "logs-*"
      default_field: "message"

flows:
  - id: hybrid_search
    steps:
      - id: semantic_search
        index: vector_knowledge
        inputs:
          - id: semantic_query
            type: text
        outputs:
          - id: semantic_matches
            type: text
      
      - id: structured_search
        index: structured_data
        filters:
          level: "error"
          timestamp:
            gte: "now-1h"
        inputs:
          - id: log_query
            type: text
        outputs:
          - id: log_matches
            type: text
```
