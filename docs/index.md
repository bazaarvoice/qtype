# Overview

**QType is a domain-specific language (DSL) for rapid prototyping of AI applications.**  
It is designed to help developers define modular, composable AI systems using a structured YAML-based specification. QType supports models, prompts, tools, retrievers, and flow orchestration, and is extensible for code generation or live interpretation.
## 🚀 Quick Start

Install QType:

```bash
pip install qtype[interpreter]
```

Create a file `hello_world.qtype.yaml` that answers a question:
```yaml
id: hello_world
flows:
  - id: chat_example
    description: A simple chat flow with OpenAI
    mode: Chat
    steps:
      - id: llm_inference_step
        model: 
          id: gpt-4
          provider: openai
          auth: 
            id: openai_auth
            type: api_key
            api_key: ${OPENAI_KEY}
        system_message: |
          You are a helpful assistant.
        inputs:
          - id: user_message
            type: ChatMessage
        outputs:
          - id: response
            type: ChatMessage
```

Put your openai api key into your `.env` file:
```
echo "OPENAI_KEY=sk...." >> .env
```

Validate it's semantic correctness:

```bash
qtype validate hello_world.qtype.yaml 
```

You should see:

```
INFO: ✅ Schema validation successful.
INFO: ✅ Model validation successful.
INFO: ✅ Language validation successful
INFO: ✅ Semantic validation successful
```

Launch the interpreter:

```bash
qtype serve hello_world.qtype.yaml`
```


And go to [http://localhost:8000/ui](http://localhost:8000/ui) to see the user interface for your application:

![Example UI](example_ui.png)


Check out the [Getting Started](./Getting%20Started/installation.md) guide to learn more.