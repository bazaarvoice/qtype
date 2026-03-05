# Scaffold a QType Project

Get a new QType project up and running in minutes by creating the required directory structure, configuring credentials, and authoring a minimal starter YAML.

---

### Step 1: Install QType

```bash
pip install qtype
```

---

### Step 2: Create the Project Directory

```bash
mkdir my-qtype-app && cd my-qtype-app
```

A typical project layout looks like this:

```
my-qtype-app/
├── .env                        # API credentials (never commit this)
└── app.qtype.yaml              # Your application spec
```

---

### Step 3: Set Up Credentials

Create a `.env` file in the project root with your AWS credentials:

```bash
# .env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

QType automatically loads `.env` at startup. Add `.env` to your `.gitignore` to avoid accidentally committing secrets.

---

### Step 4: Create the Starter YAML

Create `app.qtype.yaml` with this minimal template:

```yaml
id: my_app
description: My first QType application

models:
  - type: Model
    id: claude
    provider: aws-bedrock
    model_id: anthropic.claude-sonnet-4-20250514-v1:0

flows:
  - type: Flow
    id: chat
    variables:
      - id: question
        type: text
      - id: prompt
        type: text
      - id: answer
        type: text
    inputs:
      - question
    outputs:
      - answer
    steps:
      - id: build_prompt
        type: PromptTemplate
        template: "Answer the following question:\n{question}\n"
        inputs:
          - question
        outputs:
          - prompt

      - id: generate
        type: LLMInference
        model: claude
        inputs:
          - prompt
        outputs:
          - answer
```

---

### Step 5: Validate the Spec

```bash
qtype validate app.qtype.yaml
```

Fix any reported errors before proceeding.

---

### Step 6: Run or Serve the Application

Run a single flow from the command line:

```bash
qtype run -i '{"question": "What is QType?"}' app.qtype.yaml
```

Or serve the application as an HTTP API:

```bash
qtype serve app.qtype.yaml
```

---

### Explanation

- **`id`**: Unique identifier for the application; used in logging and the serve endpoint
- **`models`**: List of language model definitions; each model is referenced by its `id` in steps
- **`provider: aws-bedrock`**: Routes inference calls through AWS Bedrock using ambient AWS credentials
- **`PromptTemplate`**: Step that renders a string template using named inputs, producing a formatted prompt
- **`LLMInference`**: Step that sends a prompt to a language model and captures the response
- **`qtype validate`**: Parses and type-checks the YAML spec without executing any flows
- **`qtype serve`**: Starts an HTTP server exposing each flow as a REST endpoint

## See Also

- [Validate a QType Spec](../Observability%20%26%20Debugging/validate_qtype_yaml.md)
- [Serve Flows as APIs](../Qtype%20Server/serve_flows_as_apis.md)
- [Tutorial: First QType Application](../../Tutorials/01-first-qtype-application.md)
