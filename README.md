# QType

**QType is a domain-specific language (DSL) for rapid prototyping of AI applications.**  
It is designed to help developers define modular, composable AI systems using a structured YAML-based specification. QType supports models, prompts, tools, retrievers, and flow orchestration, and is extensible for code generation or live interpretation.

---

## 🚀 Getting Started

Install QType:

```bash
pip install qtype
```

Then run the built-in CLI on the provided Hello World example:

```bash
qtype validate examples/hello_world.qtype.yaml
```

You should see output confirming the file is valid according to the QType schema and passes semantic validation.

---

## 📁 Examples

See the [`examples/`](./examples/) folder for more usage examples, including:
- `hello_world.qtype.yaml`: a minimal flow with a single prompt
- `demo_with_retriever.yaml`: demonstrates use of a retriever and inputs

---

## 🤝 Contributing

We welcome contributions! Please follow the instructions in the [contribution guide](./CONTRIBUTING.md).

---

## 📄 License

This project is licensed under a **non-commercial license**.  
See the [LICENSE](./LICENSE) file for details.

---

## 🔧 Project Structure

- `qtype/` – Python package for parsing, validating, and interpreting QType specs
- `examples/` – Example `.qtype.yaml` specs
- `schema/` – JSON Schema auto-generated from the DSL
- `docs/` – Documentation (for GitHub Pages)
- `scripts/` – Developer tools and schema generation
- `tests/` – Unit and integration tests

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