# QType

**QType is a domain-specific language (DSL) for rapid prototyping of AI applications.**  
It is designed to help developers define modular, composable AI systems using a structured YAML-based specification. QType supports models, prompts, tools, retrievers, and flow orchestration, and is extensible for code generation or live interpretation.

---

## 🚀 Getting Started

Install QType:

```bash
pip install qtype
```

Set your openai key and run the [hello world example](examples/hello_world.qtype.yaml) which simply asks a model a question:
:

```bash
OPENAI_KEY=<YOUR_OPENAI_KEY> qtype run examples/hello_world.qtype.yaml
```

You'll see a prompt asking to enter the question. Type what you like and enter Ctrl+D:

```shell
INFO: 🚀 Running flow 'simple_qa'...
INFO: Starting execution of flow: simple_qa

==================================================
INPUTS REQUIRED
==================================================
Your Question (press Ctrl+D when finished): 

Hi! This is just a test of QType -- an ai dsl. What model are you?  

INFO: Executing step: answer_step
INFO: Rendered prompt template for 'answer_prompt'
INFO: Calling OpenAI model 'gpt-4o' with params: {'model': 'gpt-4o', 'messages': [{'role': 'user', 'content': 'You are a helpful assistant.\nAnswer the following question:\n\nHi! This is just a test of QType -- an ai dsl. What model are you?\n\n'}], 'temperature': 0.7, 'max_tokens': 512}
INFO: HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"

🤖 Generated Response:
------------------------------
Hello! I am an AI language model developed by OpenAI, known as ChatGPT. I'm designed to assist with a wide range of questions and tasks. How can I help you today?
------------------------------
INFO: ✅ Flow execution completed successfully.

==================================================
RESULT:
==================================================
Hello! I am an AI language model developed by OpenAI, known as ChatGPT. I'm designed to assist with a wide range of questions and tasks. How can I help you today?
==================================================
```


## 📁 Examples

See the [`examples/`](./examples/) folder for more usage examples, including:
- `hello_world.qtype.yaml`: a minimal flow with a single prompt

---

## 🤝 Contributing

Contributions welcome! Please follow the instructions in the [contribution guide](./CONTRIBUTING.md).

---

## 📄 License

This project is licensed under the **MIT License**.  
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