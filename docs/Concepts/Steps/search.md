# Search

Search steps enable information retrieval from indexed data using different search strategies. QType provides both vector-based semantic search and traditional document search capabilities, allowing applications to find relevant information based on user queries.

Search steps integrate with [Indexes](../Core/indexes.md) to perform efficient retrieval operations and can be combined with other steps to build sophisticated question-answering and information retrieval workflows.

## Rules and Behaviors

- **Index Dependency**: Search steps require a valid index reference to perform search operations
- **Query Processing**: Input queries are processed according to the search type (semantic embedding for vector search, text matching for document search)
- **Result Ranking**: Search results are automatically ranked by relevance score
- **Configurable Limits**: Number of returned results can be controlled via configuration parameters
- **Type Safety**: Search steps validate that the referenced index supports the requested search operation
- **Empty Results**: Search steps handle cases where no matching documents are found gracefully
- **Similarity Thresholds**: Vector search can filter results based on minimum similarity scores

## Vector Search

Vector search performs semantic similarity matching using embeddings to find conceptually related content.

### Component Definition

--8<-- "components/VectorSearch.md"

### Configuration

### Key Properties

- **index**: Reference to a vector index containing embedded documents
- **top_k**: Maximum number of results to return (default: 10)
- **similarity_threshold**: Minimum similarity score for results (0.0-1.0)
- **embedding_model**: Optional override for query embedding generation

## Document Search

Document search performs traditional text-based search using keyword matching and full-text search capabilities.

### Component Definition

--8<-- "components/DocumentSearch.md"

### Configuration

### Key Properties

- **index**: Reference to a document index with full-text search capabilities
- **max_results**: Maximum number of documents to return
- **search_fields**: Specific fields to search within documents
- **boost_factors**: Relevance boosting for specific fields
- **filters**: Additional filtering criteria for search results

## Related Concepts

Search steps work with [Indexes](../Core/indexes.md) for data storage and retrieval, may use [Models](../Core/model.md) for embedding generation in vector search, and integrate with [Flows](../Core/flow.md) for complex information retrieval pipelines. Results are typically consumed by other [Steps](index.md) for further processing.

## Example Usage
