
# Tutorials

- [x] Your First QType Application + auth (15 min)
- [x] Building a Stateful Chatbot (20 min)
- [x] Working with Types and Structured Data (25 min)
- [x] Adding Tools to Your Application (25 min)
- [ ] Building an AI Agent (30 min)
- [ ] Organize applications with modular YAML (includes and references)

# Example Gallery

Structure:
┌─────────────────────────────────┐
│ Example Name: "RAG System"      │
├─────────────────────────────────┤
│ • Visual diagram                │
│ • 2-3 sentence description      │
│ • Complete working code         │
│ • Key features highlighted      │
│ • Links:                        │
│   → Tutorial: "Build a RAG..."  │
│   → How-To: "Add vector search" │
│   → Reference: VectorIndex docs │
└─────────────────────────────────┘

- [x] ⚡ Simple Chatbot
- [x] ⚡ Dataflow Pipeline for LLM Calls
- [ ] ⚡ Retrieval Augmented Generation (RAG)
- [ ] ⚡ Q&A With Semantic Re-Ranking
- [ ] ⚡ Hybrid Search System
- [x] ⚡ Research Assistant
- [ ] ⚡ Collaborative Agents
- [ ] ⚡ Evaluation & Judging

# How Tos

```
# {Task as Question}

{1-2 sentence overview of the problem / approach}

### QType YAML

\`\`\`yaml
# Only the relevant YAML snippet, not complete app
{minimal snippet demonstrating the solution}
\`\`\`

### Explanation

- **{Schema Object/Type/Parameter}**: {1 line what it does}
- **{Schema Object/Type/Parameter}**: {1 line what it does}
- **{Schema Object/Type/Parameter}**: {1 line what it does}

## Complete Example

\`\`\`yaml
# Optional: include only if a full working example adds value
# Otherwise, omit this section entirely
# Use a snippet to include from the examples/ directory
\`\`\`

## See Also

- [Related How-To](../{Category}/{guide}.md)
- [Component Reference](../../components/{Component}.md)
- [Tutorial](../../Tutorials/{tutorial}.md)
- [Example](../../Gallery/{Category}/{example}.md)
```

**Language Features**
- [x] Use Environment Variables
- [x] Reference Entities by ID
- [x] Include Raw Text from Other Files
- [x] Include QType Yaml
- [ ] Use List Types
- [ ] Use Session Inputs for Sticky Variables

**Command Line Usage**
- [x] Pass Inputs On The CLI
- [x] Load Multiple Inputs from Files

**Data Processing**
- [x] Read Data from SQL databases
- [x] Read Data from files
- [ ] Read Data from Document Sources
- [x] Write Data to a File
- [x] Adjust Concurrency
- [ ] Configure Batch Processing
- [x] Invoke Other Flows
- [x] Cache Step Results
- [x] Explode Collections for Fan-Out Processing
- [x] Gather Results into a List
- [ ] Aggregate results?
- [ ] Use Echo for Debugging
- [x] Decode JSON/XML to Structured Data

**Invoke Models**
- [x] Reuse Prompts with Templates
- [x] Call Large Language Models
- [x] Create Embeddings
- [x] Configure Model Parameters (temperature, max_tokens)
- [ ] Use Memory for Conversational Context
- [ ] Switch Between Model Providers

**Authentication**
- [x] Use API Key Authentication
- [ ] Use Bearer Token Authentication
- [ ] Use OAuth2 Authentication
- [x] Configure AWS Authentication (Access Keys, Profile, Role)
- [ ] Configure Google Vertex Authentication
- [ ] Manage Secrets with Secret Manager
- [ ] AWS Secret Manager integration with SecretReference

**Observability & Debugging**
- [x] Trace Calls with Open Telemetry
- [x] Validate Qtype YAML
- [x] Visualize Application Architecture

**Data & Types**
- [ ] Use Built-In Types (`text`, `number`, `boolean`, `bytes`)
- [ ] Use Built-In Domain Types (ChatMessage, RAGDocument, RAGChunk, RAGSearchResult, Embedding, AggregateStats)
- [ ] Define Custom Types
- [ ] Extract Structured Data with FieldExtractor (JSONPath)
- [ ] Transform Data with Construct
- [ ] Work with List Types

**Tools & Integration**
- [x] Create Tools from OpenAPI Specifications
- [x] Create Tools from Python Modules
- [x] Bind Tool Inputs and Outputs

**Qtype Server**
- [x] Serve Flows as APIs
- [x] Serve Flows as UI
- [x] Use Conversational Interfaces
- [x] Serve Applications with Auto-Reload
- [x] Use Variables with UI Hints

**Chat Specific**
- [ ] Configure Memory Token Limits
- [ ] Use Conversation History in Prompts
- [ ] Persist Session Inputs Across Turns


**Retrieval Augmented Generation (RAG)**
- [ ] Convert Documents to Text (PDF, DOCX)
- [ ] Split Documents into Chunks (Configure Chunk Size and Overlap)
- [ ] Embed Document Chunks
- [ ] Populate a Vector Index
- [ ] Populate a Document Index
- [ ] Search a Document Index (Full-Text)
- [ ] Search a Vector Index (Semantic)
- [ ] Filter Search Results
- [ ] Rerank Search Results with Bedrock Reranker
- [ ] Implement Hybrid Search Strategies
- [ ] Configure Vector Index Parameters (HNSW)
- [ ] Upsert Data into Indexes


**Extension & Advanced**
- [ ] Write CLI Plugins
- [ ] Configure Step Caching with Version/Namespace

# Concepts

**Mental Model & Philosophy**
- [x] ⚡ What is QType? (elevator pitch and purpose)
- [x] ⚡ Core mental model: flows, steps, variables, and data flow
- [x] ⚡ What QType is NOT (non-goals and anti-patterns)
- [x] ⚡ When to use QType vs alternatives

**Architecture & Design**
- [ ] QType architecture: DSL → Semantic → Interpreter layers
- [ ] The loading pipeline: parse → link → resolve → check
- [ ] Dependency resolution and the symbol table
- [ ] Step execution model and executors

**Flow Processing**
- [ ] How the interpreter processes data flows
- [ ] Flow Interface Differences
- [ ] Variable scoping and lifetime in flows
- [ ] 1-to-many cardinality and fan-out patterns
- [ ] Error handling and recovery patterns
- [ ] Pipeline composition with Explode/Collect

**Typing**
- [ ] Type system: primitives, domain types, and custom types
- [ ] Type resolution and validation
- [ ] Reference resolution (IDs to objects)

**UI Streaming**
- [ ] Stream event types and their lifecycle
- [ ] SSE (Server-Sent Events) for real-time streaming
- [ ] Callback-based vs async iterator patterns
- [ ] How executors emit stream events

**Performance Concepts**
- [ ] Resource caching strategy (TTL cache for models/indexes)
- [ ] Concurrency model: BatchableStepMixin vs ConcurrentStepMixin
- [ ] Memory management and token limits

**Validation & Rules**
- [x] ⚡ Semantic validation rules by model entity

**Decision Guides**
- [ ] Vector search vs Document search vs SQL search (when to use each)
- [ ] When to use InvokeTool vs Agent
- [ ] When to use batching vs concurrent execution

# Reference

**CLI Commands**
- `qtype run` - Execute applications
- `qtype validate` - Validate YAML specs
- `qtype serve` - Serve as HTTP API
- `qtype visualize` - Generate architecture diagrams
- `qtype generate` - Generate JSON schema
- `qtype convert` - Convert OpenAPI or Python modules to tools

**YAML Specification**
- [ ] Application structure
- [ ] Flow definition
- [ ] Step types reference
- [ ] Variable types
- [ ] Model configuration
- [ ] Authentication providers
- [ ] Telemetry sinks
- [ ] Memory configuration
- [ ] Index types (Vector, Document)
- [ ] Tool types (PythonFunction, API)

**Step Types**
- [ ] Source steps (FileSource, SQLSource, DocumentSource)
- [ ] Processing steps (PromptTemplate, LLMInference, InvokeEmbedding)
- [ ] Data manipulation (Explode, Collect, Construct, FieldExtractor, Aggregate)
- [ ] Tool steps (InvokeTool, Agent)
- [ ] Search steps (VectorSearch, DocumentSearch)
- [ ] Writer steps (FileWriter, IndexUpsert)
- [ ] Conversion steps (DocToTextConverter, DocumentSplitter, DocumentEmbedder)
- [ ] Utility steps (Echo, Decoder, InvokeFlow, Reranker)

**Domain Types**
- [ ] ChatMessage, ChatContent, MessageRole
- [ ] RAGDocument, RAGChunk, RAGSearchResult
- [ ] Embedding, SearchResult
- [ ] AggregateStats

**Python API**
- [ ] QTypeFacade
- [ ] Application model
- [ ] Custom step development
- [ ] Plugin system
- [ ] Executor interface

**Model Providers**
- [ ] AWS Bedrock
- [ ] OpenAI
- [ ] Google Vertex AI
- [ ] Provider-specific parameters
- [ ] Authentication methods

**Validation & Error Reference**
- [ ] ⚡ Error catalog with error IDs
- [ ] ⚡ Structured fix hints for each error type
- [ ] ⚡ Common validation failures and resolutions
- [ ] ⚡ Error message explanations

# Quick Reference

**Cheat Sheet** (for MCP and developers)
- [ ] ⚡ Syntax at a glance
- [ ] ⚡ Most common step types with minimal examples
- [ ] ⚡ Variable binding patterns quick reference
- [ ] ⚡ Authentication quick reference

**Schema Summary** (structured, machine-readable)
- [ ] ⚡ Required fields at a glance
- [ ] ⚡ Step structure patterns
- [ ] ⚡ Typing rules quick reference
- [ ] ⚡ Common pitfalls summary

**Troubleshooting Guide**
- [ ] ⚡ Common error patterns and fixes
- [ ] ⚡ Debugging workflow issues
- [ ] ⚡ Quick fixes for typical mistakes
