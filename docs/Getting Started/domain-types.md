# Working with Domain Types

QType provides several built-in domain types that represent common AI and chat application data structures. These types are designed to work seamlessly across different AI providers and ensure type safety in your applications.

## Overview of Domain Types

QType includes these key domain types:

- **`ChatMessage`** - Structured chat messages with roles and content blocks
- **`ChatContent`** - Individual content blocks (text, images, etc.) within messages  
- **`Embedding`** - Vector embeddings with metadata
- **`MessageRole`** - Enumeration of message sender roles
- **`PrimitiveTypeEnum`** - Basic data types (text, image, audio, etc.)

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

```yaml
# Example: Multi-modal message with text and image
variables:
  - id: multimodal_message
    type: ChatMessage
    # Structure:
    # role: user
    # blocks:
    #   - type: text
    #     content: "What's in this image?"
    #   - type: image  
    #     content: <image_data>
    #     mime_type: "image/jpeg"
```

## Practical Examples

### Basic Chat Flow

```yaml
id: simple_chat
flows:
  - id: chat_conversation
    mode: Chat
    steps:
      - id: llm_step
        model:
          id: gpt-4
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

### Multi-Modal Chat with Images

```yaml
id: vision_chat
flows:
  - id: image_analysis
    steps:
      - id: vision_step
        model:
          id: gpt-4o
          provider: openai
          auth: openai_auth
        system_message: |
          You are a helpful assistant that can analyze images.
        inputs:
          - id: user_query
            type: ChatMessage  # Can contain both text and images
        outputs:
          - id: analysis_result
            type: ChatMessage  # Text response about the image
```

### Chat with Memory

```yaml
id: persistent_chat
memories:
  - id: conversation_memory
    token_limit: 50000
    chat_history_token_ratio: 0.8

flows:
  - id: remembered_conversation
    mode: Chat
    steps:
      - id: chat_step
        model: gpt-4
        memory: conversation_memory  # Maintains ChatMessage history
        inputs:
          - id: current_message
            type: ChatMessage
        outputs:
          - id: contextual_response
            type: ChatMessage
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

### RAG with Embeddings

```yaml
id: rag_system
models:
  - id: embedder
    provider: openai
    model_id: text-embedding-3-large
    dimensions: 3072
    auth: openai_auth

indexes:
  - id: knowledge_base
    name: documents
    embedding_model: embedder

flows:
  - id: rag_query
    steps:
      - id: search_step
        index: knowledge_base
        inputs:
          - id: query
            type: text
        outputs:
          - id: search_results
            type: array
            items:
              type: Embedding  # Found embeddings with metadata
      
      - id: generate_step
        model: gpt-4
        system_message: |
          Use these search results to answer the question:
          {{search_results}}
        inputs:
          - id: user_question
            type: ChatMessage
        outputs:
          - id: rag_response
            type: ChatMessage
```

## Primitive Types in Domain Context

--8<-- "components/PrimitiveTypeEnum.md"

### Using Primitive Types with Domain Types

Domain types often contain primitive types as components:

```yaml
# ChatContent uses PrimitiveTypeEnum for content type
variables:
  - id: text_message
    type: ChatMessage
    # Contains ChatContent with type: text
    
  - id: image_message  
    type: ChatMessage
    # Contains ChatContent with type: image
    
  - id: audio_message
    type: ChatMessage
    # Contains ChatContent with type: audio
```

### Multi-Modal Content Types

```yaml
id: multimedia_chat
flows:
  - id: handle_media
    steps:
      - id: process_input
        inputs:
          - id: media_message
            type: ChatMessage
            # Can contain any combination:
            # - text content blocks
            # - image content blocks  
            # - audio content blocks
            # - video content blocks
            # - file content blocks
```

## Advanced Patterns

### Custom Variables with Domain Types

```yaml
id: advanced_chat_system

# Define reusable variables
variables:
  - id: system_prompt
    type: ChatMessage  # System role message
    
  - id: user_query
    type: ChatMessage  # User input
    
  - id: tool_results
    type: ChatMessage  # Tool execution results
    
  - id: final_response
    type: ChatMessage  # Final AI response

flows:
  - id: complex_interaction
    steps:
      - id: tool_step
        tools:
          - web_search
        inputs:
          - user_query
        outputs:
          - tool_results  # ChatMessage with tool role
          
      - id: synthesis_step
        model: gpt-4
        inputs:
          - system_prompt
          - user_query
          - tool_results
        outputs:
          - final_response
```

### Type Validation and Error Handling

QType automatically validates domain types:

```yaml
# ✅ Valid ChatMessage structure
flows:
  - id: valid_flow
    steps:
      - inputs:
          - id: proper_message
            type: ChatMessage  # Must have role + blocks

# ❌ This would fail validation
flows:
  - id: invalid_flow  
    steps:
      - inputs:
          - id: wrong_structure
            type: ChatMessage  # Missing required fields
```

### Converting Between Types

```yaml
id: type_conversion
flows:
  - id: text_to_chat
    steps:
      - id: convert_step
        template: |
          {
            "role": "user",
            "blocks": [
              {
                "type": "text",
                "content": "{{input_text}}"
              }
            ]
          }
        inputs:
          - id: input_text
            type: text
        outputs:
          - id: chat_message
            type: ChatMessage
```

## Best Practices

### 1. Use Appropriate Roles
```yaml
# ✅ Clear role assignment
variables:
  - id: system_instructions
    type: ChatMessage  # role: system
    
  - id: user_input
    type: ChatMessage  # role: user
    
  - id: ai_output
    type: ChatMessage  # role: assistant
```

### 2. Structure Multi-Modal Content
```yaml
# ✅ Well-organized multi-modal message
variables:
  - id: rich_message
    type: ChatMessage
    # Structure:
    # role: user
    # blocks:
    #   - type: text, content: "Analysis request"
    #   - type: image, content: <image>, mime_type: "image/png"
    #   - type: text, content: "What do you see?"
```

### 3. Maintain Type Consistency
```yaml
# ✅ Consistent typing across flow
flows:
  - id: typed_flow
    steps:
      - id: step1
        inputs: [user_message]    # ChatMessage
        outputs: [processed_msg]  # ChatMessage
        
      - id: step2  
        inputs: [processed_msg]   # Same type
        outputs: [final_response] # ChatMessage
```

### 4. Use Embeddings with Metadata
```yaml
# ✅ Rich embedding with context
variables:
  - id: contextual_embedding
    type: Embedding
    # Contains:
    # vector: [0.1, 0.2, ...]
    # source_text: "Original document text"
    # metadata: {"document_id": "doc123", "section": "introduction"}
```

## Troubleshooting Common Issues

### Type Mismatch Errors
```yaml
# ❌ Wrong type assignment
variables:
  - id: message
    type: text  # Should be ChatMessage for chat flows

# ✅ Correct type assignment  
variables:
  - id: message
    type: ChatMessage
```

### Missing Content Structure
```yaml
# ❌ Incomplete ChatMessage (missing blocks)
# This would fail validation

# ✅ Complete ChatMessage structure
# role: user
# blocks:
#   - type: text
#     content: "Hello"
```

### Embedding Dimension Mismatches
```yaml
# ✅ Ensure embedding model dimensions match index
models:
  - id: embedder
    model_id: text-embedding-3-large
    dimensions: 3072  # Must match index expectations
    
indexes:
  - id: vector_store
    embedding_model: embedder  # Uses same dimensions
```

Domain types in QType provide a robust foundation for building AI applications with proper data structure, type safety, and multi-modal capabilities. They integrate seamlessly with the broader QType ecosystem while maintaining compatibility across different AI providers.
