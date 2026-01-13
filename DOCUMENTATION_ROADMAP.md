
# Tutorials

- [ ] Your First QType Application (15 min)
- [ ] Configuration and Authentication (20 min) 
    All the examples need AWS/OpenAI credentials, but auth is never taught
    It's implicitly used but never explained
    A beginner would be stuck at "how do I configure my API key?"
- [ ] Building a Stateful Chatbot (20 min)
- [ ] Working with Types and Structured Data (25 min)
- [ ] Adding Tools to Your Application (25 min)
- [ ] Building an AI Agent (30 min)

# Patterns & Examples

┌─────────────────────────────────┐
│ Pattern Name: "RAG System"      │
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

**Conversational AI**
- [ ] ⚡ Simple Chatbot
- [ ] ⚡ Multi-Turn Reasoning Agent
- [ ] ⚡ Customer Support Bot

**RAG & Document Processing**
- [ ] ⚡ Complete RAG System (ingestion + chat)
- [ ] ⚡ Semantic Search Q&A
- [ ] ⚡ Multi-Modal Document Analysis
- [ ] ⚡ Hybrid Search System

**Data Processing**
- [ ] ⚡ ETL Pipeline
- [ ] ⚡ Batch Document Classification
- [ ] ⚡ Structured Data Extraction
- [ ] ⚡ CSV Processing at Scale

**Multi-Agent Systems**
- [ ] ⚡ Research Assistant
- [ ] ⚡ Collaborative Agents

**Specialized**
- [ ] ⚡ Evaluation & Judging
- [ ] ⚡ Content Moderation

# How Tos

**Getting Started**
- [ ] Configure authentication and API keys
- [ ] Set up environment variables and secrets
- [ ] Adjust model parameters (memory, temperature, token, system messages)

**Configuration & Organization**
- [ ] Organize applications with modular YAML (includes and references)
- [ ] Reference entities by ID
- [ ] Use session inputs for sticky variables
- [ ] Manage secrets with Secret Manager

**Observability & Debugging**
- [ ] Validate YAML specifications
- [ ] Visualize application architecture
- [ ] Add telemetry (Phoenix, Langfuse, Prometheus)

**Data Sources**
- [ ] Read from SQL databases
- [ ] Read from files (CSV, JSON, text)
- [ ] Load Documents

**Data & Types**
- [ ] Work with domain types (ChatMessage, RAGDocument, etc.)
- [ ] Define custom types
- [ ] Extract structured data with FieldExtractor
- [ ] Transform data with Construct
- [ ] Aggregate data from multiple records

**Document Processing**
- [ ] Convert documents to text (PDF, DOCX)
- [ ] Split documents into chunks
- [ ] Embed document chunks
- [ ] Configure chunking strategies

**Search & Retrieval**
- [ ] Add vector search to an application
- [ ] Perform document search (full-text)
- [ ] Configure search filters
- [ ] Rerank search results
- [ ] Implement hybrid search strategies

**Index Management**
- [ ] Create and configure vector indexes
- [ ] Create and configure document indexes
- [ ] Upsert data into indexes

**Tools & Integration**
- [ ] Create tools from OpenAPI specifications
- [ ] Create tools from Python modules
- [ ] Configure tool parameters and outputs

**Flows & Orchestration**
- [ ] Organize multi-flow applications
- [ ] Invoke flows from other flows
- [ ] Share resources across flows

**Data Output**
- [ ] Write results to files
- [ ] Batch write operations

**Performance & Optimization**
- [ ] Configure concurrency for parallel processing
- [ ] Enable caching to reduce costs
- [ ] Batch process large datasets

**Deployment**
- [ ] Serve applications via HTTP API
- [ ] Deploy with Docker

**Extension & Advanced**
- [ ] Create custom step types
- [ ] Write QType plugins

# Explanation

**Mental Model & Philosophy**
- [ ] ⚡ What is QType? (elevator pitch and purpose)
- [ ] ⚡ Core mental model: flows, steps, variables, and data flow
- [ ] ⚡ Design constraints and assumptions
- [ ] ⚡ What QType is NOT (non-goals and anti-patterns)
- [ ] ⚡ When to use QType vs alternatives

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
- [ ] ⚡ Semantic validation rules explained
- [ ] ⚡ Why each validation rule exists
- [ ] ⚡ How to satisfy validation requirements

**Decision Guides**
- [ ] Vector search vs Document search vs SQL search (when to use each)
- [ ] When to use InvokeTool vs Agent
- [ ] When to use batching vs concurrent execution

**Common Mistakes & Anti-Patterns**
- [ ] ⚡ Common pitfalls and how to avoid them
- [ ] ⚡ Anti-patterns and why they fail
- [ ] ⚡ Debugging common misconceptions

# Reference

**CLI Commands**
- `qtype run` - Execute applications
- `qtype validate` - Validate YAML specs
- `qtype serve` - Serve as HTTP API
- `qtype visualize` - Generate architecture diagrams
- `qtype generate schema` - Generate JSON schema
- `qtype convert api` - Convert OpenAPI to tools
- `qtype convert module` - Convert Python modules to tools

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
