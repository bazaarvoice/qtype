# QType

**QType is a domain-specific language (DSL) for rapid prototyping of AI applications.**  
It is designed to help developers define modular, composable AI systems using a structured YAML-based specification. QType supports models, prompts, tools, retrievers, and flow orchestration, and is extensible for code generation or live interpretation.

---

## 🚀 Quick Start

Install QType:

```bash
pip install qtype[interpreter]
```

Create a file `hello_world_bedrock.qtype.yaml` that uses AWS Bedrock for a simple chat session:
```yaml
id: hello_world
description: "A simple hello world app using Bedrock, taking a ChatMessage as input."

flows:
  - id: simple_flow
    steps:
      - id: llm_inference_step
        model: 
          id: amazon.nova-lite-v1:0
          provider: aws-bedrock
        system_message: |
          You are a helpful assistant.
        inputs:
          - id: user_message
            type: ChatMessage
        outputs:
          - id: response_message
            type: ChatMessage
```

Validate that the file matches the spec:
```
qtype validate hello_world_bedrock.qtype.yaml
```

You should see:
```
INFO: ✅ Schema validation successful.
INFO: ✅ Model validation successful.
INFO: ✅ Language validation successful
INFO: ✅ Semantic validation successful
```

Finally, launch the prototype as an api:
```
AWS_PROFILE=your_profile qtype run api hello_world_bedrock.qtype.yaml 
```
and visit [http://localhost:8000/docs](http://localhost:8000/docs) to interact with it.


## 📄 License

This project is licensed under the **MIT License**.  
See the [LICENSE](./LICENSE) file for details.

---

## 🧠 Philosophy

QType is built around modularity, traceability, and rapid iteration. It aims to empower developers to quickly scaffold ideas into usable AI applications without sacrificing maintainability or control.

Stay tuned for upcoming features like:
- Integrated OpenTelemetry tracing
- Validation via LLM-as-a-judge
- UI hinting via input display types
- Flow state switching and conditional routing

---

Happy hacking with QType! 🛠️