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

models:
  - type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo

flows:
  - type: Flow
    id: chat_example
    description: A simple chat flow with OpenAI
    interface:
      type: Conversational
    variables:
      - id: user_message
        type: ChatMessage
      - id: response
        type: ChatMessage
    inputs:
      - user_message
    outputs:
      - response
    steps:
      - type: LLMInference
        id: llm_inference_step
        model: gpt-4
        system_message: "You are a helpful assistant."
        inputs:
          - user_message
        outputs:
          - response
```

Put your OpenAI API key into your `.env` file:
```
echo "OPENAI_API_KEY=sk-..." >> .env
```

Validate its semantic correctness:

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
qtype serve hello_world.qtype.yaml
```


And go to [http://localhost:8000/ui](http://localhost:8000/ui) to see the user interface for your application:

![Example UI](example_ui.png)


Check out the [Tutorials](Tutorials/01-first-qtype-application.md) guide to learn more.