# {{ cookiecutter.project_name }}

A QType AI application. This project was generated from the
[QType cookiecutter template](https://github.com/bazaarvoice/qtype/tree/main/template).

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An OpenAI API key (set `OPENAI_API_KEY` in a `.env` file)

## Setup

```bash
# Install dependencies
uv sync

# Create a .env file with your API key
echo "OPENAI_API_KEY=sk-..." > .env
```

## Validate the application

Check your QType YAML for syntax errors, reference issues, and semantic problems:

```bash
qtype validate {{ cookiecutter.__slug }}.qtype.yaml
```

## Run the application

Start the QType server with auto-reload enabled for development:

```bash
qtype serve --reload {{ cookiecutter.__slug }}.qtype.yaml
```

The server will start at <http://localhost:8000>. Open your browser to see the
interactive UI.

## Run from the command line

Invoke a flow directly without starting the server:

```bash
qtype run {{ cookiecutter.__slug }}.qtype.yaml \
  --flow ask \
  --input '{"user_name": "Alice", "user_question": "What is machine learning?"}'
```

## Generate tool definitions from Python

Regenerate `{{ cookiecutter.__slug }}.tools.qtype.yaml` from
`{{ cookiecutter.__module }}/tools.py` whenever you add or modify tool functions:

```bash
qtype convert module {{ cookiecutter.__module }}.tools \
  -o {{ cookiecutter.__slug }}.tools.qtype.yaml
```

## Project structure

```
{{ cookiecutter.__slug }}/
├── {{ cookiecutter.__module }}/        # Python tools package
│   ├── __init__.py
│   └── tools.py                        # Custom tool functions
├── {{ cookiecutter.__slug }}.qtype.yaml        # Main QType application
├── {{ cookiecutter.__slug }}.tools.qtype.yaml  # Generated tool definitions
├── pyproject.toml                      # Project metadata and dependencies
├── Dockerfile                          # Container image definition
└── .vscode/
    └── launch.json                     # VS Code debug configurations
```

## Docker

Build and run the application in a container:

```bash
docker build -t {{ cookiecutter.__slug }} .

# Pass API keys at runtime (never bake secrets into the image)
docker run -p 8000:8000 --env-file .env {{ cookiecutter.__slug }}
```
