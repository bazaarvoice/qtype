# Tutorial: Build a Conversational Chatbot

**What you'll learn:** In 20 minutes, you'll add memory to your QType application and create a chatbot that remembers previous messages in the conversation.

**What you'll build:** A stateful chatbot that maintains conversation history and provides contextual responses.

## Before You Begin

You should have completed:
- **[Tutorial 1: Your First QType Application](01-first-qtype-application.md)** - Understanding applications, models, flows, and steps

Make sure you have:
- QType installed: `pip install qtype[interpreter]`
- An OpenAI API key (or AWS Bedrock access)
- Your `my_first_app.qtype.yaml` from Tutorial 1
- 20 minutes

---

## Understanding Stateful vs Stateless Applications

In Tutorial 1, you built a **stateless** application - it processed each question independently with no memory of previous interactions:

```
You: What is 2+2?
AI: 4.

You: What about that times 3?
AI: I don't know what "that" refers to.  ❌
```

Today you'll build a **stateful** chatbot that remembers the conversation:

```
You: What is 2+2?
AI: 4.

You: What about that times 3?  
AI: 12. I multiplied the previous answer (4) by 3.  ✅
```

This requires two new concepts: **Memory** and **Conversational Interface**.

---

## Flow Interfaces: Complete vs Conversational

QType flows have two interface types that control how they process requests:

### Complete Interface (Tutorial 1)

- **Default behavior** - You don't need to specify it
- Processes one request → one response
- No memory between requests
- Each request is independent
- Like a REST API call or function call

**Example use cases:**
- Simple Q&A
- Data transformation
- Single-step calculations

**In YAML (optional to specify):**
```yaml
flows:
  - type: Flow
    id: simple_flow
    interface:
      type: Complete  # Optional - this is the default
```

### Conversational Interface (This Tutorial)

- **Explicit configuration** - You must specify it
- Maintains conversation history
- Each message adds to the context
- Enables memory and multi-turn interactions
- Like a chat session

**Example use cases:**
- Chatbots
- Virtual assistants
- Contextual Q&A systems

**In YAML (required):**
```yaml
flows:
  - type: Flow
    id: chat_flow
    interface:
      type: Conversational  # Required for memory
```

**Key Rule:** Memory only works with Conversational interface. If your flow uses memory, it must declare `interface.type: Conversational`.

---

## Part 1: Add Memory to Your Application (5 minutes)

### Create Your Chatbot File

Create a new file called `my_chatbot.qtype.yaml`. Start by copying your application structure from Tutorial 1:

```yaml
id: my_chatbot
description: A conversational chatbot with memory

models:
  - type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo
    inference_params:
      temperature: 0.7
```

**What's different:** We changed the `id` and `description` to reflect that this is a chatbot.

---

### Add Memory Configuration

Now add a memory configuration *before* the `flows:` section:

```yaml
memories:
  - id: chat_memory
    token_limit: 50000
    chat_history_token_ratio: 0.7
```

**What this means:**
- `memories:` - Section for memory configurations (new concept!)
- `id: chat_memory` - A nickname you'll use to reference this memory
- `token_limit: 50000` - Maximum total tokens (includes conversation + system messages)
- `chat_history_token_ratio: 0.7` - Reserve 70% of tokens for conversation history

**Why tokens matter:**  
LLMs have a maximum context window (how much text they can "see" at once). GPT-4-turbo has a 128k token limit, but we're using 50k here for cost efficiency. The `chat_history_token_ratio` ensures the AI always has room to see enough conversation history while leaving space for its response.

**Check your work:**
1. Save the file
2. Validate: `qtype validate my_chatbot.qtype.yaml`
3. Should pass ✅ (even though we haven't added flows yet)

---

## Part 2: Create a Conversational Flow (7 minutes)

### Set Up the Conversational Flow

Add this flow definition:

```yaml
flows:
  - type: Flow
    id: chat_flow
    description: Main chat flow with conversation memory
    interface:
      type: Conversational
    variables:
      - id: user_message
        type: ChatMessage
      - id: response_message
        type: ChatMessage
    inputs:
      - user_message
    outputs:
      - response_message
```

**New concepts explained:**

**`interface.type: Conversational`** - This is the key difference from Tutorial 1!
- Tells QType this flow maintains conversation state
- Automatically manages message history
- Required when using memory in LLMInference steps

**`ChatMessage` type** - A special domain type for chat applications
- Represents a single message in a conversation
- Contains both the message content and metadata (role, timestamp, etc.)
- Different from the simple `text` type you used in Tutorial 1
- Learn more: [Domain Types Reference](../components/ChatMessage.md)

**Why two variables?**  
- `user_message` - What the user types
- `response_message` - What the AI responds
- QType tracks both in memory for context

**Check your work:**
1. Validate: `qtype validate my_chatbot.qtype.yaml`
2. Should still pass ✅

---

### Add the Chat Step

Add the LLM inference step that connects to your memory:

```yaml
    steps:
      - type: LLMInference
        id: chat_step
        model: gpt-4
        memory: chat_memory
        system_message: "You are a helpful assistant. Be friendly and conversational."
        inputs:
          - user_message
        outputs:
          - response_message
```

**What's new from Tutorial 1:**

**`memory: chat_memory`** - Links this step to the memory configuration
- Automatically sends conversation history with each request
- Updates memory after each exchange
- This line is what enables "remembering" previous messages

**`system_message` with personality** - Unlike Tutorial 1's generic message, this shapes the AI's behavior for conversation

**Check your work:**
1. Validate: `qtype validate my_chatbot.qtype.yaml`
2. Should pass ✅

---

## Part 3: Set Up and Test (8 minutes)

### Configure Authentication

Create `.env` in the same folder (or update your existing one):

```
OPENAI_API_KEY=sk-your-key-here
```

**Already using AWS Bedrock?** Replace the model configuration with:
```yaml
models:
  - type: Model
    id: claude
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
```

And update the step to use `model: claude`.

---

### Start the Chat Interface

Unlike Tutorial 1 where you used `qtype run` for one-off questions, conversational applications work better with the web interface:

```bash
qtype serve my_chatbot.qtype.yaml
```

**What you'll see:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Visit:** [http://localhost:8000/ui](http://localhost:8000/ui)

You should see a chat interface with your application name at the top.

---

### Test Conversation Memory

Try this conversation to see memory in action:

```
You: My name is Alex and I love pizza.
AI: Nice to meet you, Alex! Pizza is delicious...

You: What's my name?
AI: Your name is Alex!  ✅

You: What food do I like?
AI: You mentioned you love pizza!  ✅
```

**Experiment:** 
1. Refresh the page - memory resets (new session)
2. Try a multi-step math problem:
   - "Remember the number 42"
   - "Now multiply that by 2"  
   - Does it remember 42?

---

## Part 4: Understanding What's Happening (Bonus)

### The Memory Lifecycle

Here's what happens when you send a message:

```
User: "What's my name?"
  ↓
QType: Get conversation history from memory
  ↓
Memory: Returns previous messages (including "My name is Alex")
  ↓
QType: Combines system message + history + new question
  ↓
LLM: Processes full context → "Your name is Alex!"
  ↓
QType: Saves new exchange to memory
  ↓
User: Sees response
```

**Key insight:** The LLM itself has no memory - QType handles this by:
1. Storing all previous messages
2. Sending relevant history with each new question
3. Managing token limits automatically

---

### Why Token Management Matters

Your `chat_history_token_ratio: 0.7` setting means:

- **70% of tokens** → Conversation history (up to 35,000 tokens with our 50k limit)
- **30% of tokens** → System message + AI response (15,000 tokens)

If the conversation gets too long, QType automatically:
1. Keeps recent messages
2. Drops older messages
3. Ensures the AI always has enough tokens to respond

**Try it:** Have a very long conversation (50+ exchanges). Notice how the AI forgets early messages but remembers recent context.

---

## What You've Learned

Congratulations! You've mastered:

✅ **Memory configuration** - Storing conversation state  
✅ **Conversational flows** - Multi-turn interactions  
✅ **ChatMessage type** - Domain-specific data types  
✅ **Token management** - Controlling context window usage  
✅ **Web interface** - Using `qtype serve` for chat applications  

---

## Compare: Tutorial 1 vs Tutorial 2

| Feature | Tutorial 1 (Complete) | Tutorial 2 (Conversational) |
|---------|----------------------|----------------------------|
| **Interface** | `Complete` (default) | `Conversational` (explicit) |
| **Memory** | None | `chat_memory` configuration |
| **Variable Types** | `text` (primitive) | `ChatMessage` (domain type) |
| **Testing** | `qtype run` (command line) | `qtype serve` (web UI) |
| **Use Case** | One-off questions | Multi-turn conversations |

---

## Next Steps

Now that you can build conversational applications:

**Want to dive deeper?**
- [Memory Concept](../Concepts/Core/memory.md) - Advanced memory strategies
- [ChatMessage Reference](../How-To%20Guides/Data%20Types/domain-types.md) - Full type specification
- [Flow Interfaces](../Concepts/Core/flow.md) - Complete vs Conversational

---

## Complete Code

Here's your complete `my_chatbot.qtype.yaml`:

```yaml
id: my_chatbot
description: A conversational chatbot with memory

models:
  - type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo
    inference_params:
      temperature: 0.7

memories:
  - id: chat_memory
    token_limit: 50000
    chat_history_token_ratio: 0.7

flows:
  - type: Flow
    id: chat_flow
    description: Main chat flow with conversation memory
    interface:
      type: Conversational
    variables:
      - id: user_message
        type: ChatMessage
      - id: response_message
        type: ChatMessage
    inputs:
      - user_message
    outputs:
      - response_message
    steps:
      - type: LLMInference
        id: chat_step
        model: gpt-4
        memory: chat_memory
        system_message: "You are a helpful assistant. Be friendly and conversational."
        inputs:
          - user_message
        outputs:
          - response_message
```

**Download:** See a similar example at [examples/hello_world_chat.qtype.yaml](https://github.com/bazaarvoice/qtype/blob/main/examples/hello_world_chat.qtype.yaml)

---

## Common Questions

**Q: Why do I need `ChatMessage` instead of `text`?**  
A: `ChatMessage` includes metadata (role, attachments) that QType uses to properly format conversation history for the LLM. The `text` type is for simple strings without this context.

**Q: Can I have multiple memory configurations?**  
A: Yes! You can define multiple memories in the `memories:` section and reference different ones in different flows or steps.

**Q: Can I use memory with the `Complete` interface?**  
A: No - memory only works with `Conversational` interface. Complete flows are stateless by design. If you need to remember information between requests, you must use the Conversational interface.

**Q: When should I use Complete vs Conversational?**  
A: Use Complete for independent requests (data transformation, single questions, API-like behavior). Use Conversational when you need context from previous interactions (chatbots, assistants, multi-step conversations).

**Q: How do I clear memory during a conversation?**  
A: Currently, you need to start a new session (refresh the page in the UI). Programmatic memory clearing is planned for a future release.
