# Build a Conversational Chatbot

**Time:** 20 minutes  
**Prerequisites:** [Tutorial 1: Your First QType Application](01-first-qtype-application.md)  
**Example:** [`02_conversational_chat.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/02_conversational_chat.qtype.yaml)

**What you'll learn:** 

* Stateful flows with memory
* Using the web ui
* Domain types

**What you'll build:** A stateful chatbot that maintains conversation history and provides contextual responses.

---

## Background: A Quick Note on Flows

Flows are effectively data pipelines -- they accept input values and produce output values. 
The flow will execute for each input it receives.

Thus, for a conversational AI, each message from the user is one execution of the flow.

Flows are inherently _stateless_: no data is stored between executions though they can use tools, apis, or memory to share data.

In this example, we'll use memory to let the flow remember previous chat messages from both the user and the LLM.


## Part 1: Add Memory to Your Application (5 minutes)

### Create Your Chatbot File

Create a new file called `02_conversational_chat.qtype.yaml`. Let's use bedrock for this example, but you could also use OpenAI as in the previous tutorial:

```yaml
id: 02_conversational_chat
description: A conversational chatbot with memory

models:

models:
  - type: Model
    id: nova_lite
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 512

```

---

### Add Memory Configuration

Now add a memory configuration *before* the `flows:` section:

```yaml
memories:
  - id: chat_memory
    token_limit: 10000
```

**What this means:**

- `memories:` - Section for memory configurations (new concept!)
- `id: chat_memory` - A nickname you'll use to reference this memory
- `token_limit: 10000` - Maximum total tokens to have in the memory

**Check your work:**

1. Save the file
2. Validate: `qtype validate 02_conversational_chat.qtype.yaml`
3. Should pass ✅ (even though we haven't added flows yet)

---

## Part 2: Create a Conversational Flow (7 minutes)

### Set Up the Conversational Flow

Add this flow definition:

```yaml
flows:
  - type: Flow
    id: simple_chat_example
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

**`ChatMessage` type** - A special domain type for chat applications

- Represents a single message in a conversation
- Contains structured blocks (text, images, files, etc.) and metadata
- Different from the simple `text` type used in stateless applications

**ChatMessage Structure:**

```yaml
ChatMessage:
  blocks:
    - type: text
      content: "Hello, how can I help?"
    - type: image
      url: "https://example.com/image.jpg"
  role: assistant  # or 'user', 'system'
  metadata:
    timestamp: "2025-11-08T10:30:00Z"
```

The `blocks` list allows multimodal messages (text + images + files), while `role` indicates who sent the message. QType automatically handles this structure when managing conversation history.


**Why two variables?**

- `user_message` - What the user types
- `response_message` - What the AI responds
- QType tracks both in memory for context

**`interface.type: Conversational`**

This tells QType that the flow should be served as a conversation. When you type `qtype serve` (covered below) this ensures that the ui shows a chat interface instead of just listing inputs and outputs.


**Check your work:**

1. Validate: `qtype validate 02_conversational_chat.qtype.yaml`
2. Should still pass ✅

---

### Add the Chat Step

Add the LLM inference step that connects to your memory:

```yaml
    steps:
      - id: llm_inference_step
        type: LLMInference
        model: nova_lite
        system_message: "You are a helpful assistant."
        memory: chat_memory
        inputs:
          - user_message
        outputs:
          - response_message
```

**What's new:**

**`memory: chat_memory`** - Links this step to the memory configuration
- Automatically sends conversation history with each request
- Updates memory after each exchange
- This line is what enables "remembering" previous messages

**`system_message` with personality** - Unlike the previous generic message, this shapes the AI's behavior for conversation

**Check your work:**

1. Validate: `qtype validate 02_conversational_chat.qtype.yaml`
2. Should pass ✅

---

## Part 3: Set Up and Test (8 minutes)

### Configure Authentication

Create `.env` in the same folder (or update your existing one):

```
AWS_PROFILE=your-aws-profile
```

**Using OpenAI?** Replace the model configuration with:
```yaml
auths:
  - type: api_key
    id: openai_auth
    api_key: ${OPENAI_KEY}
    host: https://api.openai.com
models:
  - type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo
    auth: openai_auth
    inference_params:
      temperature: 0.7
```

And:

- update the step to use `model: gtp-4`.
- update your `.env` file to have `OPENAI_KEY`

---

### Start the Chat Interface

Unlike the previous tutorial where you used `qtype run` for one-off questions, conversational applications work better with the web interface:

```bash
qtype serve 02_conversational_chat.qtype.yaml
```

**What you'll see:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Visit:** [http://localhost:8000/ui](http://localhost:8000/ui)

You should see a chat interface with your application name at the top. Give it a chat!

![the ui showing a chat interface](example_chat.png)



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

Refreshing the page creates a new session and the memory is removed.

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


**The memory is keyed on the user session** -- it's not accessible by other visitors to the page. 

---

## What You've Learned

Congratulations! You've mastered:

✅ **Memory configuration** - Storing conversation state  
✅ **Conversational flows** - Multi-turn interactions  
✅ **ChatMessage type** - Domain-specific data types  
✅ **Web interface** - Using `qtype serve` for chat applications  

---

## Next Steps

**Reference the complete example:**

- [`02_conversational_chat.qtype`](https://github.com/bazaarvoice/qtype/blob/main/examples/02_conversational_chat.qtype) - Full working example

**Learn more:**

- [Memory Concept](../Concepts/Core/memory.md) - Advanced memory strategies
- [ChatMessage Reference](../How-To%20Guides/Data%20Types/domain-types.md) - Full type specification
- [Flow Interfaces](../Concepts/Core/flow.md) - Complete vs Conversational

---

## Common Questions

**Q: Why do I need `ChatMessage` instead of `text`?**  
A: `ChatMessage` includes metadata (role, attachments) that QType uses to properly format conversation history for the LLM. The `text` type is for simple strings without this context.

**Q: Can I have multiple memory configurations?**  
A: Yes! You can define multiple memories in the `memories:` section and reference different ones in different flows or steps.

**Q: Can I use memory with the `Complete` interface?**  
A: No - memory only works with `Conversational` interface. Complete flows are stateless by design. If you need to remember information between requests, you must use the Conversational interface.

**Q: When should I use Complete vs Conversational?**  
A: Use Complete for streaming single responses from an llm. Use Conversational when you need context from previous interactions (chatbots, assistants, multi-step conversations).

**Q: How do I clear memory during a conversation?**  
A: Currently, you need to start a new session (refresh the page in the UI).
