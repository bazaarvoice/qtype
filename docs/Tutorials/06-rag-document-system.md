# Build a RAG Document System

**Time:** 30 minutes  
**Prerequisites:** Tutorials 1-5  
**Example:** [`rag.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/rag.qtype.yaml)

**What you'll learn:** Build a production-ready Retrieval Augmented Generation (RAG) system with document ingestion and conversational search.

**What you'll build:** A complete RAG application with two flows: one to ingest documents into a vector database, and one to chat with those documents using contextual retrieval.

## Prerequisites Checklist

Before starting, verify your environment is ready:

**Required Software:**

- QType installed: `pip install qtype[interpreter]`
- Docker installed and running: `docker --version`
- AWS CLI configured: `aws sts get-caller-identity`

**Required Accounts/Keys:**

- AWS account with Bedrock access
- Your AWS profile set: `export AWS_PROFILE=your-profile-name`

**Required Python Packages:**

- HuggingFace reader: `uv add llama-index-readers-huggingface-fs --optional interpreter`

**Verify Your Setup:**

```bash
# Check Docker is running
docker ps

# Check AWS credentials
aws sts get-caller-identity

# Check Python packages
pip list | grep llama-index-readers-huggingface-fs
```

**Time Required:** 30 minutes

---

## What is RAG?

**RAG (Retrieval Augmented Generation)** solves a key problem with LLMs: they can only answer questions about information they were trained on.

**Without RAG:**
```
You: What was discussed in last week's meeting?
AI: I don't have access to your meeting notes.  ❌
```

**With RAG:**
```
You: What was discussed in last week's meeting?
AI: According to your notes, the team discussed Q4 roadmap...  ✅
```

### How RAG Works

```
┌─────────────────────────────────────────────────────────┐
│ 1. INGESTION (One-time setup)                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Documents → Split → Embed → Store in Vector DB        │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 2. RETRIEVAL (Every query)                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Question → Search Vector DB → Get Relevant Chunks     │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 3. GENERATION (Every query)                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Question + Context → LLM → Answer                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key concepts:**

- **Embeddings** - Convert text to numbers (vectors) that capture meaning
- **Vector Database** - Store and search embeddings by similarity
- **Retrieval** - Find the most relevant document chunks for a question
- **Context** - Provide retrieved chunks to the LLM for grounding

---

## Part 1: Setup (5 minutes)

### Start Qdrant Vector Database

We'll use Qdrant for vector storage. Start it with Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

**What this does:**

- Runs Qdrant on `http://localhost:6333`
- Persists data in `./qdrant_storage/`
- Ready for connections immediately

**Verify it's running:**
```bash
curl http://localhost:6333/
```

You should see Qdrant version info.

---

### Install HuggingFace Reader

Our example loads documents from HuggingFace datasets:

```bash
uv add llama-index-readers-huggingface-fs --optional interpreter
```

**What this installs:**

- LlamaIndex HuggingFace reader for loading datasets
- Required for the `DocumentSource` step in our ingestion flow

---

### Configure AWS Credentials

The example uses AWS Bedrock for embeddings and generation. Set your profile:

```bash
export AWS_PROFILE=your-profile-name
```

Or configure via AWS CLI:
```bash
aws configure
```

**Models we'll use:**

- `amazon.titan-embed-text-v2:0` - Generate embeddings (1024 dimensions)
- `amazon.nova-lite-v1:0` - Generate conversational responses

---

## Part 2: Understanding the Application (5 minutes)

### Two-Flow Architecture

RAG applications need two separate workflows:

**Flow 1: `document_ingestion`** (Run once or periodically)
```
Load docs → Split → Embed → Store in vector DB
```

**Flow 2: `rag_chat`** (Run for each user query)
```
Question → Search vectors → Build context → Generate answer
```

**Why separate flows?**

- Ingestion is expensive (run once, reuse forever)
- Chat is fast (only searches + generates)
- Different interface types (Complete vs Conversational)
- Can update documents without restarting chat

---

### What We're Building

Create `rag_example.qtype.yaml`:

````yaml
id: rag_example
description: |
  End-to-end RAG system with document ingestion and conversational search.
````

**Our dataset:**

- LlamaIndex Q&A pairs from HuggingFace (1235 instruction-output pairs)
- Source: `AlignmentLab-AI/llama-index` dataset
- Perfect for testing RAG with structured knowledge

---

## Part 3: Configure Shared Resources (5 minutes)

### Add Authentication

````yaml
auths:
  - type: aws
    id: aws_auth
    profile_name: ${AWS_PROFILE}
````

**What this does:**

- Uses your AWS credentials for Bedrock API calls
- References the `AWS_PROFILE` environment variable
- Shared by both models

---

### Add Models

````yaml
models:
  # Embedding model for vector search
  - type: EmbeddingModel
    id: titan_embed_v2
    provider: aws-bedrock
    model_id: amazon.titan-embed-text-v2:0
    dimensions: 1024
    auth: aws_auth
  
  # Generative model for chat responses
  - type: Model
    id: claude_sonnet
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 2048
    auth: aws_auth
````

**Key differences:**

- `EmbeddingModel` - Converts text → vectors (used for search)
- `Model` - Generates text responses (used for chat)
- Both use the same `aws_auth`

**Why separate models?**

- Embedding models optimize for semantic similarity
- Generative models optimize for coherent text
- Different APIs and pricing

---

### Add Vector Index

````yaml
indexes:
  - type: VectorIndex
    module: llama_index.vector_stores.qdrant.QdrantVectorStore
    id: rag_index
    name: documents
    embedding_model: titan_embed_v2
    args:
      collection_name: documents
      url: http://localhost:6333
      api_key: ""
````

**New concepts:**

- `VectorIndex` - Configuration for vector storage
- `module` - LlamaIndex vector store implementation
- `embedding_model` - Links to our Titan embedding model
- `args` - Passed to QdrantVectorStore constructor

**Why empty `api_key`?**

- Local Qdrant doesn't need authentication
- Library validation requires the field (known bug)
- For production, use a real API key

---

## Part 4: Build the Ingestion Flow (5 minutes)

### Create the Flow Structure

````yaml
flows:
  - type: Flow
    id: document_ingestion
    description: Load, split, embed, and index documents
    
    variables:
      - id: raw_document
        type: RAGDocument
      - id: document_chunk
        type: RAGChunk
      - id: embedded_chunk
        type: RAGChunk
    
    outputs:
      - embedded_chunk
````

**Built-in RAG types:**

- `RAGDocument` - A complete document with text and metadata
- `RAGChunk` - A piece of a document (after splitting)
- Both include embeddings when available

**Note:** No inputs! This flow loads data from HuggingFace directly.

---

### Step 1: Load Documents

````yaml
    steps:
      - id: load_documents
        type: DocumentSource
        reader_module: llama_index.readers.huggingface_fs.HuggingFaceFSReader
        loader_args:
          path: "datasets/AlignmentLab-AI/llama-index/modified_dataset.jsonl"
        outputs:
          - raw_document
````

**`DocumentSource` step:**

- `reader_module` - LlamaIndex reader class to use
- `loader_args` - Arguments passed to reader's `load_data()` method
- `cardinality: many` - Emits one document per record (1235 in this case)

**What this loads:**

- Each record becomes a `RAGDocument`
- Contains instruction/output Q&A pairs
- Metadata preserved for filtering

---

### Step 2: Split Documents

````yaml
      - id: split_documents
        type: DocumentSplitter
        splitter_name: "SentenceSplitter"
        chunk_size: 512
        chunk_overlap: 50
        inputs:
          - raw_document
        outputs:
          - document_chunk
````

**Why split documents?**

- LLMs have context limits (can't process 100-page documents)
- Smaller chunks = more precise retrieval
- Overlap ensures context isn't lost at boundaries

**`DocumentSplitter` parameters:**

- `splitter_name` - LlamaIndex splitter to use
- `chunk_size` - Maximum tokens per chunk
- `chunk_overlap` - Tokens shared between adjacent chunks

**Result:** 1235 documents → ~3000+ chunks (varies by document size)

---

### Step 3: Embed Chunks

````yaml
      - id: embed_chunks
        type: DocumentEmbedder
        model: titan_embed_v2
        concurrency_config:
          num_workers: 5
        inputs:
          - document_chunk
        outputs:
          - embedded_chunk
````

**`DocumentEmbedder` step:**

- Calls embedding model for each chunk
- Adds embedding vector to `RAGChunk` object
- `concurrency_config` - Process 5 chunks in parallel

**Why parallel processing?**

- Embedding 3000+ chunks sequentially is slow
- 5 workers = ~5x faster
- AWS Bedrock supports concurrent requests

**What's an embedding?**

- A 1024-dimensional vector of numbers
- Chunks with similar meanings have similar vectors
- Enables semantic search (not just keyword matching)

---

### Step 4: Store in Vector Database

````yaml
      - id: index_chunks
        type: IndexUpsert
        index: rag_index
        batch_config:
          batch_size: 25
        inputs:
          - embedded_chunk
        outputs:
          - embedded_chunk
````

**`IndexUpsert` step:**

- Stores chunks in the vector database
- `batch_config` - Insert 25 chunks per API call (more efficient)
- `outputs` - Passes through chunks (for monitoring)

**What "upsert" means:**

- Insert if new, update if exists
- Safe to re-run without duplicates
- Uses chunk ID for deduplication

---

### Run the Ingestion Flow

```bash
uv run qtype run examples/rag.qtype.yaml --flow document_ingestion
```

**Expected output:**
```
INFO: Loading documents from HuggingFace...
INFO: Loaded 1235 documents
INFO: Splitting documents...
INFO: Split into 3247 chunks
INFO: Embedding chunks (5 workers)...
INFO: Embedded 3247 chunks
INFO: Upserting to Qdrant (batch_size=25)...
INFO: ✅ Indexed 3247 chunks successfully
```

**This will take 5-10 minutes** due to embedding API calls.

**Check Qdrant:**
```bash
curl http://localhost:6333/collections/documents
```

You should see 3247 vectors in the collection.

---

## Part 5: Build the Chat Flow (5 minutes)

### Create the Flow Structure

````yaml
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
````

**Key points:**

- `interface: Conversational` - Maintains chat history (from [Build a Conversational Chatbot](02-conversational-chatbot.md))
- `ChatMessage` - Rich message type with text blocks (from [Build a Conversational Chatbot](02-conversational-chatbot.md))
- `list[RAGSearchResult]` - Built-in type for search results
- All variables flow through the pipeline

---

### Step 1: Extract Question Text

````yaml
    steps:
      - id: extract_question
        type: FieldExtractor
        json_path: "$.blocks[?(@.type == 'text')].content"
        inputs:
          - user_message
        outputs:
          - user_question
````

**Why extract?**

- `ChatMessage` contains blocks (text, images, etc.)
- We need plain text for vector search
- JSONPath filters for text-type blocks only

**What this does:**

- Input: `ChatMessage` with blocks
- Output: String with just the text content
- Handles multi-block messages automatically

---

### Step 2: Search Vector Database

````yaml
      - id: search_index
        type: VectorSearch
        index: rag_index
        default_top_k: 5
        inputs:
          - user_question
        outputs:
          - search_results
````

**`VectorSearch` step:**

- Embeds the question automatically using the index's embedding model
- Searches for similar chunks in Qdrant
- Returns top 5 most relevant chunks

**How VectorSearch Handles Embedding:**

VectorSearch automatically embeds your query using the `embedding_model` specified in the `VectorIndex` configuration. You don't need a separate DocumentEmbedder step for queries! 

```yaml
# The index configuration tells VectorSearch which model to use
indexes:
  - type: VectorIndex
    embedding_model: titan_embed_v2  # ← VectorSearch uses this

# VectorSearch automatically embeds user_question with titan_embed_v2
- type: VectorSearch
  index: rag_index  # Uses the embedding_model from this index
```

**How similarity works:**

1. Question → embedding vector (using `titan_embed_v2`)
2. Compare to all stored chunk vectors
3. Return chunks with closest vectors (cosine similarity)

**Result:**

- `list[RAGSearchResult]` with 5 chunks
- Each has text, score, and metadata
- Ordered by relevance (best first)

---

### Step 3: Build Context Prompt

````yaml
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
````

**`PromptTemplate` step:**

- Combines question + retrieved chunks into one prompt
- `{variable}` - Template variables get replaced with values
- Output is a string ready for the LLM

**Why this matters:**

- LLMs need context and question together
- Template ensures consistent formatting
- Can adjust prompt without changing code

---

### Step 4: Generate Response

````yaml
      - id: generate_response
        type: LLMInference
        model: claude_sonnet
        system_message: "You are a helpful assistant that answers questions based on provided document context. Be concise and accurate."
        inputs:
          - context_prompt
        outputs:
          - assistant_response
````

**Standard LLM inference:**

- Uses the generative model (not embedding model)
- System message guides behavior
- Returns `ChatMessage` for conversational interface

---

### Run the Chat Flow

```bash
uv run qtype serve examples/rag.qtype.yaml --flow rag_chat
```

**Open the Web UI:**
```
http://localhost:8000
```

**Try these questions:**

```
You: What is LlamaIndex?
AI: [Answers based on retrieved documentation chunks]

You: How do I create a vector index?
AI: [Provides specific instructions from the docs]

You: What embedding models are supported?
AI: [Lists models found in the documentation]
```

**What's happening:**

1. Your question → extract text
2. Text → search vectors → get 5 relevant chunks
3. Question + chunks → build prompt
4. Prompt → LLM → answer
5. Answer → displayed in chat UI

---

## Part 6: Understanding the Complete Flow (5 minutes)

### The Full Pipeline

```
USER INPUT
    ↓
┌─────────────────────────┐
│ 1. Extract Question     │  ChatMessage → text
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│ 2. Search Index         │  text → list[RAGSearchResult]
│    (embed + similarity) │  (Auto-embeds question)
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│ 3. Build Context        │  question + results → prompt
│    (template)           │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│ 4. Generate Response    │  prompt → ChatMessage
│    (LLM inference)      │
└──────────┬──────────────┘
           ↓
      USER OUTPUT
```

**Key insight:** `VectorSearch` handles embedding internally!

- You pass plain text
- It calls the embedding model automatically
- Returns already-ranked results

---

### Compare Ingestion vs Chat Flows

| Aspect | Ingestion Flow | Chat Flow |
|--------|----------------|-----------|
| **Interface** | Complete (default) | Conversational |
| **Runs** | Once (or periodically) | Every query |
| **Speed** | Slow (minutes) | Fast (seconds) |
| **Cardinality** | Many (processes 1000s of docs) | One (one question) |
| **Purpose** | Prepare data | Answer questions |
| **Cost** | High (embed everything) | Low (embed one question) |

---

## What You've Learned

Congratulations! You've mastered:

✅ **RAG architecture** - Ingestion, retrieval, generation  
✅ **Vector embeddings** - Converting text to searchable vectors  
✅ **Vector databases** - Storing and searching by similarity  
✅ **DocumentSource** - Loading documents from various sources  
✅ **DocumentSplitter** - Chunking large documents  
✅ **DocumentEmbedder** - Creating embeddings with concurrency  
✅ **IndexUpsert** - Batch insertion into vector stores  
✅ **VectorSearch** - Semantic similarity search  
✅ **Two-flow applications** - Separate ingestion and retrieval  
✅ **Production RAG patterns** - Complete end-to-end system

---

## Next Steps

**Reference the complete example:**

- [`rag.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/rag.qtype.yaml) - Full working example

**Learn more:**

- [VectorIndex Reference](../components/VectorIndex.md) - All vector store options
- [DocumentSource Reference](../components/DocumentSource.md) - Document readers
- [VectorSearch Reference](../components/VectorSearch.md) - Advanced search features

---

## Common Questions

**Q: Why separate ingestion and chat flows?**  
A: Ingestion is expensive (embedding thousands of chunks) and runs once. Chat is fast (embedding one query) and runs per request. Separating them optimizes both performance and cost.

**Q: How do I run ingestion before chat?**  
A: Always run the ingestion flow first: `uv run qtype run examples/rag.qtype.yaml --flow document_ingestion`, then start chat: `uv run qtype serve examples/rag.qtype.yaml --flow rag_chat`

**Q: Can I use different embedding models for ingestion and search?**  
A: No, you must use the same model for both. The VectorIndex configuration specifies one `embedding_model` that's used by both DocumentEmbedder (ingestion) and VectorSearch (queries).

**Q: How do I check if documents were ingested successfully?**  
A: Query Qdrant directly: `curl http://localhost:6333/collections/documents` to see collection stats and document count.

**Q: What if my documents are too large?**  
A: Adjust the DocumentSplitter `chunk_size` parameter. Smaller chunks (256-512 tokens) work better for precise retrieval. Larger chunks (1024+ tokens) preserve more context.

**Q: How do I improve answer quality?**  
A: Try: (1) Adjust `default_top_k` to retrieve more chunks, (2) Improve your system message to enforce context-only answers, (3) Experiment with chunk size and overlap, (4) Use metadata filters to narrow search scope.

**Q: Can I add memory to the chat flow?**  
A: Yes! Add a `memories:` section and reference it in the LLMInference step with `memory: chat_memory`. This lets the chatbot remember conversation history.

---

## Congratulations! 🎉

You've completed the QType tutorial series! You now know how to:

- Build stateless and stateful applications
- Work with tools and function calling
- Process data in pipelines
- Compose multi-flow applications
- Build production RAG systems

**Ready for more?** Check out the [How-To Guides](../How-To%20Guides/) for advanced patterns and production deployments.

---

## Production Considerations

### Ingestion Optimization

**Problem:** Ingesting large document collections is expensive.

**Solutions:**

1. **Incremental updates:**

- Only ingest new/changed documents
- Use document IDs for deduplication
- Track last ingestion timestamp

2. **Increase concurrency:**

````yaml
   concurrency_config:
     num_workers: 20  # More parallel embedding calls
````

3. **Larger batches:**

````yaml
   batch_config:
     batch_size: 100  # Fewer API calls to Qdrant
````

### Retrieval Optimization

**Problem:** Always returning top 5 chunks may not be optimal.

**Solutions:**

1. **Adjust retrieval count:**

- Increase `default_top_k` to retrieve more chunks
- More context can improve answer quality

2. **Filter by metadata:**

- Use the `filters` field to narrow search by document properties
- Filters are passed to the underlying vector store

3. **Rerank results:**

- Add a post-processing step after VectorSearch
- Use LLM to re-score and reorder retrieved chunks

### Response Quality

**Problem:** LLM makes up information not in context.

**Solutions:**

1. **Stronger system message:**

````yaml
   system_message: |
     ONLY answer based on the provided context.
     If the context doesn't contain the answer, say "I don't know."
     Do NOT make up information.
````

2. **Show sources:**

- Include chunk metadata in response
- Link to original documents
- Add citation markers

3. **Lower temperature:**

````yaml
   inference_params:
     temperature: 0.3  # More deterministic, less creative
````

---

## Common Issues and Solutions

### Issue: "Collection not found"

**Cause:** Chat flow ran before ingestion flow.

**Solution:**
```bash
# Always run ingestion first
uv run qtype run examples/rag.qtype.yaml --flow document_ingestion

# Then run chat
uv run qtype serve examples/rag.qtype.yaml --flow rag_chat
```

---

### Issue: "No relevant results found"

**Cause:** Question embedding doesn't match document embeddings.

**Solutions:**

1. Check embedding model matches:

````yaml
   # Index and search must use same model
   embedding_model: titan_embed_v2
````

2. Increase `top_k`:

````yaml
   default_top_k: 10  # Get more candidates
````

3. Check document content:

```bash
   curl http://localhost:6333/collections/documents/points/scroll
```

---

### Issue: "Ingestion is too slow"

**Cause:** Embedding 1000s of chunks sequentially.

**Solutions:**

1. Increase workers:

````yaml
   concurrency_config:
     num_workers: 10  # Careful: API rate limits!
````

2. Use faster embedding model:

````yaml
   model_id: amazon.titan-embed-text-v1:0  # v1 is faster than v2
````

3. Process in batches:

- Split documents into smaller sets
- Run ingestion flow multiple times

---

### Issue: "Qdrant connection failed"

**Cause:** Qdrant isn't running.

**Solution:**
```bash
# Check if Qdrant is running
curl http://localhost:6333/

# If not, start it
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

---

## Try These Extensions

### 1. Adjust Search Results

Retrieve more results for broader context:

````yaml
- id: search_index
  type: VectorSearch
  index: rag_index
  default_top_k: 10  # Get more results
````

### 2. Add Memory to Chat Flow

Remember conversation history:

````yaml
memories:
  - id: chat_memory
    token_limit: 50000

# In LLMInference step:
- id: generate_response
  type: LLMInference
  model: claude_sonnet
  memory: chat_memory
````

### 3. Use Different Vector Store

Switch to Pinecone or Weaviate:

````yaml
indexes:
  - type: VectorIndex
    module: llama_index.vector_stores.pinecone.PineconeVectorStore
    id: rag_index
    embedding_model: titan_embed_v2
    args:
      api_key: ${PINECONE_API_KEY}
      environment: "us-west1-gcp"
      index_name: "my-index"
````

### 4. Add File Upload

Let users upload their own documents:

````yaml
- id: load_documents
  type: DocumentSource
  reader_module: llama_index.readers.file.SimpleDirectoryReader
  loader_args:
    input_dir: "user_uploads/"
````

### 5. Add Document Metadata

Enrich documents with custom metadata during ingestion:

````yaml
- id: load_documents
  type: DocumentSource
  reader_module: llama_index.readers.file.SimpleDirectoryReader
  loader_args:
    input_dir: "user_uploads/"
    file_metadata:
      doc_type: "user_upload"
      uploaded_by: "user123"
````

---

## Complete Code

Here's the complete RAG application:

````yaml
id: rag_example
description: |
  End-to-end RAG system with document ingestion and conversational search.

auths:
  - type: aws
    id: aws_auth
    profile_name: ${AWS_PROFILE}

models:
  - type: EmbeddingModel
    id: titan_embed_v2
    provider: aws-bedrock
    model_id: amazon.titan-embed-text-v2:0
    dimensions: 1024
    auth: aws_auth
  
  - type: Model
    id: claude_sonnet
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 2048
    auth: aws_auth

indexes:
  - type: VectorIndex
    module: llama_index.vector_stores.qdrant.QdrantVectorStore
    id: rag_index
    name: documents
    embedding_model: titan_embed_v2
    args:
      collection_name: documents
      url: http://localhost:6333
      api_key: ""

flows:
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
    
    steps:
      - id: extract_question
        type: FieldExtractor
        json_path: "$.blocks[?(@.type == 'text')].content"
        inputs:
          - user_message
        outputs:
          - user_question
      
      - id: search_index
        type: VectorSearch
        index: rag_index
        default_top_k: 5
        inputs:
          - user_question
        outputs:
          - search_results
      
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
      
      - id: generate_response
        type: LLMInference
        model: claude_sonnet
        system_message: "You are a helpful assistant that answers questions based on provided document context. Be concise and accurate."
        inputs:
          - context_prompt
        outputs:
          - assistant_response

  - type: Flow
    id: document_ingestion
    description: Load, split, embed, and index documents
    
    variables:
      - id: raw_document
        type: RAGDocument
      - id: document_chunk
        type: RAGChunk
      - id: embedded_chunk
        type: RAGChunk
    
    outputs:
      - embedded_chunk
    
    steps:
      - id: load_documents
        type: DocumentSource
        reader_module: llama_index.readers.huggingface_fs.HuggingFaceFSReader
        loader_args:
          path: "datasets/AlignmentLab-AI/llama-index/modified_dataset.jsonl"
        outputs:
          - raw_document
      
      - id: split_documents
        type: DocumentSplitter
        splitter_name: "SentenceSplitter"
        chunk_size: 512
        chunk_overlap: 50
        inputs:
          - raw_document
        outputs:
          - document_chunk
      
      - id: embed_chunks
        type: DocumentEmbedder
        model: titan_embed_v2
        concurrency_config:
          num_workers: 5
        inputs:
          - document_chunk
        outputs:
          - embedded_chunk
      
      - id: index_chunks
        type: IndexUpsert
        index: rag_index
        batch_config:
          batch_size: 25
        inputs:
          - embedded_chunk
        outputs:
          - embedded_chunk
````

---

## Next Steps

**Explore More:**

- [VectorIndex Reference](../components/VectorIndex.md) - All vector store options
- [DocumentSource Reference](../components/DocumentSource.md) - Document readers
- [VectorSearch Reference](../components/VectorSearch.md) - Advanced search features
- [RAG Best Practices](../How-To%20Guides/rag-best-practices.md) - Production patterns

**Build Your Own:**

- Load your own documents (PDFs, Word files, etc.)
- Experiment with different embedding models
- Try different chunk sizes and overlap
- Add metadata filtering to search
- Implement multi-modal RAG (text + images)

---

## Congratulations! 🎉

You've completed the QType tutorial series! You now know how to:

- Build stateless and stateful applications
- Work with tools and agents
- Process data in pipelines
- Compose multi-flow applications
- Build production RAG systems

**Ready for more?** Check out the [How-To Guides](../How-To%20Guides/) for advanced patterns and production deployments.
