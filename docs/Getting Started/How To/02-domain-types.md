# Use Domain Types

QType provides several built-in domain types that represent common AI and chat application data structures. 

## Overview of Domain Types

QType includes these key domain types:

- **`ChatMessage`** - Structured chat messages with roles and content blocks
- **`ChatContent`** - Individual content blocks (text, images, etc.) within messages  
- **`Embedding`** - Vector embeddings with metadata
- **`MessageRole`** - Enumeration of message sender roles

These types help you build robust AI applications with proper data structure and validation.

## ChatMessage: The Foundation of Conversational AI

--8<-- "components/ChatMessage.md"

### Understanding ChatMessage Structure

`ChatMessage` is a composite type that represents a single message in a conversation:

```yaml
# Basic chat message structure
variables:
  - id: user_input
    type: ChatMessage
    # Will contain: role + list of content blocks
    
  - id: ai_response  
    type: ChatMessage
    # AI's response with assistant role
```

### Message Roles

--8<-- "components/MessageRole.md"

The `MessageRole` enum defines who sent the message:

- **`user`** - End user input
- **`assistant`** - AI model response  
- **`system`** - System instructions/context
- **`tool`** - Tool execution results
- **`function`** - Function call results (legacy)
- **`developer`** - Developer notes/debugging
- **`model`** - Direct model output
- **`chatbot`** - Chatbot-specific role

### Content Blocks

--8<-- "components/ChatContent.md"

Each `ChatMessage` contains one or more `ChatContent` blocks:

## Practical Examples

### Basic Chat Flow

The following creates a simple chat experience that is multi-modal: since `ChatMessage` contains mupltiple blocks, the blocks can be of different multimedia types.

```yaml
id: simple_chat
flows:
  - id: chat_conversation
    mode: Chat
    steps:
      - id: llm_step
        model:
          id: gpt-4o
          provider: openai
          auth:
            id: openai_auth
            type: api_key
            api_key: ${OPENAI_KEY}
        system_message: |
          You are a helpful AI assistant.
        inputs:
          - id: user_message
            type: ChatMessage  # User's input message
        outputs:
          - id: assistant_response
            type: ChatMessage  # AI's response message
```

## Working with Embeddings

--8<-- "components/Embedding.md"

### Basic Embedding Usage

```yaml
id: embedding_example
models:
  - id: text_embedder
    provider: openai
    model_id: text-embedding-3-large
    dimensions: 3072
    auth: openai_auth

flows:
  - id: create_embeddings
    steps:
      - id: embed_step
        model: text_embedder
        inputs:
          - id: source_text
            type: text
        outputs:
          - id: text_embedding
            type: Embedding  # Vector + metadata
```
