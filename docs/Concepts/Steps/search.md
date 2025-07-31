# Search

Search steps enable information retrieval from indexed data using different search strategies. QType provides both vector-based semantic search and traditional document search capabilities, allowing applications to find relevant information based on user queries.

Search steps integrate with [Indexes](../Concepts/index-concept.md) to perform efficient retrieval operations and can be combined with other steps to build sophisticated question-answering and information retrieval workflows.

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

```yaml
steps:
  - id: semantic_search
    type: VectorSearch
    index: knowledge_base
    inputs:
      - id: user_query
        type: text
    outputs:
      - id: relevant_documents
        type: text
    top_k: 5
    similarity_threshold: 0.7
```

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

```yaml
steps:
  - id: keyword_search
    type: DocumentSearch
    index: document_collection
    inputs:
      - id: search_terms
        type: text
    outputs:
      - id: matching_documents
        type: text
    max_results: 10
    search_fields: ["title", "content", "tags"]
```

### Key Properties

- **index**: Reference to a document index with full-text search capabilities
- **max_results**: Maximum number of documents to return
- **search_fields**: Specific fields to search within documents
- **boost_factors**: Relevance boosting for specific fields
- **filters**: Additional filtering criteria for search results

## Related Concepts

Search steps work with [Indexes](../Concepts/index-concept.md) for data storage and retrieval, may use [Models](../Concepts/model.md) for embedding generation in vector search, and integrate with [Flows](../Concepts/flow.md) for complex information retrieval pipelines. Results are typically consumed by other [Steps](../Concepts/step.md) for further processing.

## Example Usage

### Basic Semantic Search

```yaml
id: semantic_qa_system

indexes:
  - id: knowledge_base
    type: vector
    embedding_model: text-embedding-ada-002
    documents:
      - path: "docs/"
        format: markdown

flows:
  - id: answer_question
    steps:
      - id: find_relevant_info
        type: VectorSearch
        index: knowledge_base
        inputs:
          - id: user_question
            type: text
        outputs:
          - id: context_documents
            type: text
        top_k: 3
        similarity_threshold: 0.75
      
      - id: generate_answer
        type: LLMInference
        model: gpt-4o
        system_message: "Answer the question based on the provided context."
        inputs:
          - id: question
            type: text
          - id: context
            type: text
        outputs:
          - id: answer
            type: text
```

### Document Search with Filtering

```yaml
id: document_finder

indexes:
  - id: document_collection
    type: document
    documents:
      - path: "reports/"
        format: pdf
      - path: "articles/"
        format: html

flows:
  - id: find_documents
    steps:
      - id: search_reports
        type: DocumentSearch
        index: document_collection
        inputs:
          - id: search_query
            type: text
        outputs:
          - id: found_documents
            type: text
        max_results: 20
        search_fields: ["title", "content", "summary"]
        filters:
          - field: "document_type"
            value: "report"
          - field: "publication_date"
            range: 
              from: "2024-01-01"
              to: "2024-12-31"
```

### Hybrid Search Strategy

```yaml
id: hybrid_search_system

flows:
  - id: comprehensive_search
    steps:
      - id: semantic_search
        type: VectorSearch
        index: vector_index
        inputs:
          - id: query
            type: text
        outputs:
          - id: semantic_results
            type: text
        top_k: 10
        similarity_threshold: 0.6
      
      - id: keyword_search
        type: DocumentSearch
        index: text_index
        inputs:
          - id: query
            type: text
        outputs:
          - id: keyword_results
            type: text
        max_results: 10
        search_fields: ["title", "content"]
      
      - id: merge_results
        type: PythonFunctionTool
        module_path: "search_utils"
        function_name: "merge_and_deduplicate"
        inputs:
          - id: semantic_matches
            type: text
          - id: keyword_matches
            type: text
        outputs:
          - id: combined_results
            type: text
      
      - id: rank_final_results
        type: PythonFunctionTool
        module_path: "search_utils"
        function_name: "rank_by_relevance"
        inputs:
          - id: all_results
            type: text
          - id: original_query
            type: text
        outputs:
          - id: ranked_results
            type: text
```

### Search with Post-Processing

```yaml
id: intelligent_search

flows:
  - id: search_and_analyze
    steps:
      - id: initial_search
        type: VectorSearch
        index: knowledge_base
        inputs:
          - id: user_query
            type: text
        outputs:
          - id: raw_results
            type: text
        top_k: 15
      
      - id: filter_relevance
        type: LLMInference
        model: gpt-4o-mini
        system_message: "Score each document for relevance to the query (0-10)."
        inputs:
          - id: query
            type: text
          - id: documents
            type: text
        outputs:
          - id: scored_documents
            type: text
      
      - id: extract_key_points
        type: LLMInference
        model: gpt-4o
        system_message: "Extract key points from the most relevant documents."
        inputs:
          - id: relevant_docs
            type: text
        outputs:
          - id: key_information
            type: text
      
      - id: synthesize_response
        type: LLMInference
        model: gpt-4o
        system_message: "Synthesize the key information into a comprehensive answer."
        inputs:
          - id: original_question
            type: text
          - id: extracted_points
            type: text
        outputs:
          - id: final_answer
            type: text
```
