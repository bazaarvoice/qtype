# Building a RAG (Retrieval Augmented Generation) Chatbot

This example demonstrates how to build a complete RAG system that can answer questions based on a knowledge base. RAG combines document retrieval with language models to provide accurate, context-aware responses grounded in your data.

We'll create a system that loads 1,235 LlamaIndex documentation Q&A pairs from HuggingFace, indexes them in a vector database, and enables conversational queries over that knowledge base.

## What is RAG?

**RAG (Retrieval Augmented Generation)** enhances language models by:

1. **Retrieving** relevant documents from a knowledge base
2. **Augmenting** the LLM prompt with retrieved context
3. **Generating** accurate answers based on that context

This prevents hallucinations and grounds responses in factual data.

## Prerequisites

Before starting, you'll need:

### 1. Qdrant Vector Database

Install and run Qdrant locally using Docker:

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

For more details, see the [Qdrant Quick Start](https://qdrant.tech/documentation/quickstart/).

### 2. Create the Vector Collection

Qdrant will automatically create the collection when you run the ingestion flow, or you can create it manually:

```bash
curl -X PUT 'http://localhost:6333/collections/documents' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "vectors": {
      "size": 1024,
      "distance": "Cosine"
    }
  }'
```

**Note:** We use dimension 1024 because AWS Bedrock Titan Embed Text v2 produces 1024-dimensional vectors.

### 3. AWS Credentials

Configure AWS credentials for Bedrock access:

```bash
aws configure
# or for SSO:
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

## Step 1: Configure Authentication

First, set up AWS authentication for Bedrock:

```yaml
auths:
  - type: aws
    id: aws_auth
    profile_name: ${AWS_PROFILE}  # Uses AWS_PROFILE env var
```

This allows QType to access AWS Bedrock for embeddings and LLM inference.

## Step 2: Define the Models

We need two types of models for RAG:

### Embedding Model

Converts text into vectors for semantic search:

```yaml
models:
  - type: EmbeddingModel
    id: titan_embed_v2
    provider: aws-bedrock
    model_id: amazon.titan-embed-text-v2:0
    dimensions: 1024
    auth: aws_auth
```

**Key Points:**
- `dimensions: 1024` - Titan v2 produces 1024-dimensional embeddings
- Used for both document indexing and query embedding

### Generative Model

Produces natural language responses:

```yaml
  - type: Model
    id: claude_sonnet
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 2048
    auth: aws_auth
```

## Step 3: Configure the Vector Index

Define the Qdrant vector store:

```yaml
indexes:
  - type: VectorIndex
    module: llama_index.vector_stores.qdrant.QdrantVectorStore
    id: rag_index
    name: documents
    embedding_model: titan_embed_v2
    args:
      collection_name: documents
      url: http://localhost:6333
      api_key: ""  # Empty for local Qdrant
```

**Important:**
- `collection_name: documents` - Must match the collection you created
- `embedding_model: titan_embed_v2` - Links to our embedding model
- `api_key: ""` - Required (even empty) due to a library validation requirement

## Step 4: Document Ingestion Flow

The ingestion flow loads, chunks, embeds, and indexes documents:

```yaml
flows:
  - type: Flow
    id: document_ingestion
    description: Load LlamaIndex Q&A pairs from HuggingFace, split, embed, and index documents
    
    variables:
      - id: raw_document
        type: RAGDocument
      - id: document_chunk
        type: RAGChunk
      - id: embedded_chunk
        type: RAGChunk
    
    outputs:
      - embedded_chunk
```

### Step 4.1: Load Documents from HuggingFace

```yaml
    steps:
      - id: load_documents
        type: DocumentSource
        reader_module: llama_index.readers.huggingface_fs.HuggingFaceFSReader
        loader_args:
          path: "datasets/AlignmentLab-AI/llama-index/modified_dataset.jsonl"
        outputs:
          - raw_document
```

**What Happens:**
- Uses HuggingFace's filesystem API to stream documents
- Loads 1,235 LlamaIndex Q&A pairs directly from HuggingFace
- No local file storage required

### Step 4.2: Split Documents into Chunks

```yaml
      - id: split_documents
        type: DocumentSplitter
        splitter_name: "SentenceSplitter"
        chunk_size: 512
        chunk_overlap: 50
        inputs:
          - raw_document
        outputs:
          - document_chunk
```

**Why Chunking?**
- Large documents exceed context windows
- Smaller chunks improve retrieval precision
- `chunk_overlap: 50` maintains context across boundaries

### Step 4.3: Generate Embeddings

```yaml
      - id: embed_chunks
        type: DocumentEmbedder
        model: titan_embed_v2
        concurrency_config:
          num_workers: 5
        inputs:
          - document_chunk
        outputs:
          - embedded_chunk
```

**Performance:**
- `num_workers: 5` - Processes 5 chunks concurrently
- Speeds up embedding generation significantly

### Step 4.4: Index in Qdrant

```yaml
      - id: index_chunks
        type: IndexUpsert
        index: rag_index
        batch_config:
          batch_size: 25
        inputs:
          - embedded_chunk
        outputs:
          - embedded_chunk
```

**Batching:**
- Uploads 25 chunks at a time to Qdrant
- Balances throughput and memory usage

## Step 5: RAG Chat Flow

The chat flow retrieves context and generates responses:

```yaml
  - type: Flow
    id: rag_chat
    description: Chat with the document collection using RAG
    
    interface:
      type: Conversational
    
    variables:
      - id: user_message
        type: ChatMessage
      - id: user_question
        type: text
      - id: search_results
        type: list[RAGSearchResult]
      - id: context_prompt
        type: text
      - id: assistant_response
        type: ChatMessage
    
    inputs:
      - user_message
    outputs:
      - assistant_response
```

### Step 5.1: Extract User Question

```yaml
    steps:
      - id: extract_question
        type: FieldExtractor
        json_path: "$.blocks[?(@.type == 'text')].content"
        inputs:
          - user_message
        outputs:
          - user_question
```

**Purpose:**
- Extracts plain text from the ChatMessage structure
- Uses JSONPath to filter text content blocks

### Step 5.2: Search the Vector Index

```yaml
      - id: search_index
        type: VectorSearch
        index: rag_index
        default_top_k: 5
        inputs:
          - user_question
        outputs:
          - search_results
```

**How It Works:**
1. Embeds the user's question using `titan_embed_v2`
2. Performs cosine similarity search in Qdrant
3. Returns top 5 most relevant chunks

### Step 5.3: Build Context Prompt

```yaml
      - id: build_prompt
        type: PromptTemplate
        template: |
          You are a helpful assistant that answers questions based on the provided context.
          
          Context from documents:
          {search_results}
          
          User question: {user_question}
          
          Please provide a detailed answer based on the context above. If the context doesn't contain relevant information, say so.
        inputs:
          - search_results
          - user_question
        outputs:
          - context_prompt
```

**Prompt Engineering:**
- Clearly separates context from question
- Instructs the model to acknowledge when context is insufficient
- Prevents hallucination

### Step 5.4: Generate Response

```yaml
      - id: generate_response
        type: LLMInference
        model: claude_sonnet
        system_message: "You are a helpful assistant that answers questions based on provided document context. Be concise and accurate."
        inputs:
          - context_prompt
        outputs:
          - assistant_response
```

**Final Step:**
- LLM generates answer using retrieved context
- `system_message` reinforces context-grounded behavior

## Complete Example

Here's the full RAG configuration:

```yaml
--8<-- "../examples/rag.qtype.yaml"
```

You can download it [here](https://github.com/bazaarvoice/qtype/blob/main/examples/rag.qtype.yaml).

## The Architecture

Here's a visual representation of the complete RAG system:

```mermaid
--8<-- "Examples/rag.mmd"
```

The diagram shows:
- **rag_chat flow** (left-right): The conversational interface with user interaction
- **document_ingestion flow** (top-down): The linear pipeline for loading and indexing documents
- **Shared Resources**: Models and authentication used by both flows

## Running the RAG System

### Step 1: Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Step 2: Run Document Ingestion

This loads and indexes all documents (takes a few minutes):

```bash
uv run python -m qtype.cli run examples/rag.qtype.yaml --flow document_ingestion
```

You'll see progress as documents are loaded, chunked, embedded, and indexed:

```
INFO: Loaded 1235 documents
INFO: Successfully upserted 25 items to vector index in batch
INFO: Successfully upserted 25 items to vector index in batch
...
```

### Step 3: Start the Chat Server

```bash
qtype serve examples/rag.qtype.yaml --flow rag_chat
```

### Step 4: Open the Chat UI

Visit [http://localhost:8000/ui](http://localhost:8000/ui)

## Try It Out

Ask questions about LlamaIndex:

- "How do I create a vector index in LlamaIndex?"
- "What is the difference between a query engine and a chat engine?"
- "How do I configure custom embeddings?"
- "What callback handlers are available in LlamaIndex?"

Notice how the responses are:
- **Accurate** - Based on real documentation
- **Cited** - Grounded in retrieved context
- **Specific** - Contains code examples and details

## Understanding the Data Flow

### Ingestion (One-Time)
```
HuggingFace Dataset 
  → DocumentSource (load)
  → DocumentSplitter (chunk)
  → DocumentEmbedder (vectorize)
  → IndexUpsert (store in Qdrant)
```

### Query (Every Chat Turn)
```
User Question
  → FieldExtractor (extract text)
  → VectorSearch (retrieve relevant chunks)
  → PromptTemplate (build context prompt)
  → LLMInference (generate answer)
  → User
```

## Advanced Customization

### Adjust Retrieval Settings

Retrieve more or fewer chunks:

```yaml
- id: search_index
  type: VectorSearch
  index: rag_index
  default_top_k: 10  # Retrieve top 10 instead of 5
```

### Change Chunking Strategy

Modify chunk size and overlap:

```yaml
- id: split_documents
  type: DocumentSplitter
  splitter_name: "SentenceSplitter"
  chunk_size: 1024  # Larger chunks
  chunk_overlap: 100  # More overlap
```

### Use Different Embeddings

Switch to a different embedding model:

```yaml
models:
  - type: EmbeddingModel
    id: custom_embeddings
    provider: openai
    model_id: text-embedding-3-large
    dimensions: 3072
```

**Important:** Update the Qdrant collection dimensions to match!

### Add Reranking

Improve retrieval quality with a reranker:

```yaml
- id: rerank_results
  type: Reranker
  model: cohere-rerank-v3
  top_n: 5
  inputs:
    - search_results
  outputs:
    - reranked_results
```

## Monitoring and Debugging

### Check Qdrant Collection

View collection stats:

```bash
curl http://localhost:6333/collections/documents
```

### View Retrieved Context

Add a debug step to see what's being retrieved:

```yaml
- id: debug_context
  type: Echo
  inputs:
    - search_results
```

### Enable Telemetry

Add OpenTelemetry tracking:

```yaml
telemetry:
  id: rag_telemetry
  endpoint: http://localhost:6006/v1/traces
```

Then run `phoenix serve` and visit [http://localhost:6006](http://localhost:6006).

## Production Considerations

### Use Qdrant Cloud

For production, switch to hosted Qdrant:

```yaml
indexes:
  - type: VectorIndex
    module: llama_index.vector_stores.qdrant.QdrantVectorStore
    id: rag_index
    name: documents
    embedding_model: titan_embed_v2
    args:
      collection_name: documents
      url: https://your-cluster.qdrant.io
      api_key: ${QDRANT_API_KEY}
```

### Scale Embedding Generation

Increase concurrency for faster ingestion:

```yaml
- id: embed_chunks
  type: DocumentEmbedder
  model: titan_embed_v2
  concurrency_config:
    num_workers: 20  # Process 20 chunks at once
```

### Implement Caching

Cache frequently retrieved chunks to reduce latency.

### Add Metadata Filtering

Filter results by metadata:

```yaml
- id: search_index
  type: VectorSearch
  index: rag_index
  default_top_k: 5
  filters:
    category: ["tutorial", "api-reference"]
```

## Learn More

- [DocumentSource Component](../components/DocumentSource.md) - Loading documents
- [VectorSearch Component](../components/VectorSearch.md) - Semantic search
- [IndexUpsert Component](../components/IndexUpsert.md) - Vector indexing
- [RAG Concepts](../Concepts/rag.md) - Deep dive into RAG architecture

## Next Steps

Try extending this example:

1. **Add your own documents** - Replace the HuggingFace dataset with your data
2. **Implement hybrid search** - Combine vector search with keyword search
3. **Add citations** - Include source references in responses
4. **Multi-modal RAG** - Index images and text together
5. **Conversation memory** - Add context from previous turns

RAG opens up powerful possibilities for building AI systems that are accurate, trustworthy, and grounded in your data!
