# QType

**QType is a domain-specific language (DSL) for rapid prototyping of AI applications.**  
It is designed to help developers define modular, composable AI systems using a structured YAML-based specification. QType supports models, prompts, tools, retrievers, and flow orchestration, and is extensible for code generation or live interpretation.

---

## 🚀 Quick Start

Install QType:

```bash
pip install qtype[interpreter]
```

Create a file `hello_world.qtype.yaml` that executes a single chat question:
```yaml
id: hello_world
flows:
  - id: simple_qa_flow
    steps:
      - id: llm_inference_step
        model: 
          id: gpt-4o
          provider: openai
          auth: 
            id: openai_auth
            type: api_key
            api_key: ${OPENAI_KEY}
        system_message: |
          You are a helpful assistant.
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: response_message
            type: text
```

Put your openai api key into your `.env` file:
```
echo "OPENAI_KEY=sk...." >> .env
```

Validate that the file matches the spec:
```
qtype validate hello_world.qtype.yaml
```

You should see:
```
INFO: ✅ Schema validation successful.
INFO: ✅ Model validation successful.
INFO: ✅ Language validation successful
INFO: ✅ Semantic validation successful
```

Finally,execute the flow.
```
qtype run flow '{"prompt":"What is the airspeed of a laden swallow?"}' hello_world.qtype.yaml 
```

You should see (something similar to):

```
INFO: Executing flow: simple_qa_flow

The airspeed of a laden swallow is a humorous reference from the movie "Monty Python and the Holy Grail." In the film, the question is posed as "What is the airspeed velocity of an unladen swallow?" The joke revolves around the absurdity and specificity of the question, and it doesn't have a straightforward answer. However, if you're curious about the real-life airspeed of a swallow, the European Swallow (Hirundo rustica) typically flies at around 11 meters per second, or 24 miles per hour, when unladen. The concept of a "laden" swallow is part of the humor, as it would depend on what the swallow is carrying and is not a standard measurement.
```

---

See the [full docs](https://bazaarvoice.github.io/qtype/) for more examples and guides.

## 🤝 Contributing

Contributions welcome! Please follow the instructions in the [contribution guide](https://bazaarvoice.github.io/qtype/contributing/).

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


[![Generate JSON Schema](https://github.com/bazaarvoice/qtype/actions/workflows/github_workflows_generate-schema.yml/badge.svg)](https://github.com/bazaarvoice/qtype/actions/workflows/github_workflows_generate-schema.yml) [![Publish to PyPI](https://github.com/bazaarvoice/qtype/actions/workflows/publish-pypi.yml/badge.svg)](https://github.com/bazaarvoice/qtype/actions/workflows/publish-pypi.yml)