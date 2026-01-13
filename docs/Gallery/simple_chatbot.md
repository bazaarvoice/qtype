# Simple Chatbot

## Overview

A friendly conversational chatbot with memory that maintains context across multiple conversation turns. This example demonstrates the minimal setup needed to create a stateful chatbot using AWS Bedrock, perfect for getting started with conversational AI applications.

## Architecture

```mermaid
--8<-- "Gallery/simple_chatbot.mermaid"
```

## Complete Code

```yaml
--8<-- "../examples/conversational_ai/simple_chatbot.qtype.yaml"
```

## Key Features

- **Conversational Interface**: This instructs the front-end to create a conversational user experience. 
- **Memory**: Conversation history buffer with `token_limit` (10,000) that stores messages and automatically flushes oldest content when limit is exceeded
- **ChatMessage Type**: Built-in domain type with `role` field (user/assistant/system) and `blocks` list for structured multi-modal content
- **LLMInference Step**: Executes model inference with optional `system_message` prepended to conversation and `memory` reference for persistent context across turns
- **Model Configuration**: Model resource with provider-specific `inference_params` including `temperature` (randomness) and `max_tokens` (response length limit)

## Running the Example

```bash
# Start the chatbot server
qtype serve examples/conversational_ai/simple_chatbot.qtype.yaml
```

## Learn More

- Tutorial: [Building a Stateful Chatbot](../../Tutorials/02_conversational_chat.md)
