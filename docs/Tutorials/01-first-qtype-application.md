# Your First QType Application 

**Time:** 15 minutes  
**Prerequisites:** None  
**Example:** [`01_hello_world.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/tutorials/01_hello_world.qtype.yaml)

**What you'll learn:** Build a working AI-powered question-answering application and understand the core concepts of QType.

**What you'll build:** A simple app that takes a question, sends it to an AI model, and returns an answer.

---

## Part 1: Your First QType File (5 minutes)

### Create the File

Create a new file called `01_hello_world.qtype.yaml` and add:

```yaml
id: 01_hello_world
description: My first QType application
```

**What this means:**

- Every QType application starts with an `id` - a unique name for your app
- The `description` helps you remember what the app does (optional but helpful)

---

### Add Your AI Model

Add these lines to your file:

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

**What this means:**

- `auths:` - different authorization credentials you will use for model invocation (if any)
- `api_key: ${OPENAI_KEY}` - the api key is read from the environment variable `OPENAI_KEY`
- `models:` - Where you configure which AI to use
- `id: gpt-4` - A nickname you'll use to refer to this model
- `model_id` - The provider's model id.
- `provider: openai` - Which AI service to use
- `temperature: 0.7` - Controls creativity (0 = focused, 1 = creative)

**Check your work:**

1. Save the file
2. Run: `qtype validate 01_hello_world.qtype.yaml`
4. You should see: `✅ Validation successful`


**Using AWS Bedrock instead?** Replace the models section with:
```yaml
models:
  - type: Model
    id: nova
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
```

And ensure your AWS credentials are configured (`aws configure`).

---

## Part 2: Add Processing Logic (5 minutes)

### Create a Flow

A "flow" is where you define what your app actually does. Add this to your file:

```yaml
flows:
  - type: Flow
    id: simple_example
    variables:
      - id: question
        type: text
      - id: formatted_prompt
        type: text
      - id: answer
        type: text
    inputs:
      - question
    outputs:
      - answer
```

**What this means:**

- `flows:` - The processing logic section
- `variables:` - Declares the data your app uses:
  - `question` - What the user asks
  - `formatted_prompt` - The formatted prompt for the AI
  - `answer` - What the AI responds
- `inputs:` and `outputs:` - Which variables go in and out

**Check your work:**

1. Validate again: `qtype validate 01_hello_world.qtype.yaml`
2. Still should see: `✅ Validation successful`

---

### Add Processing Steps

Now tell QType what to do with the question. Add this inside your flow (after `outputs:`):

```yaml
    steps:
      - id: format_prompt
        type: PromptTemplate
        template: "You are a helpful assistant. Answer the following question:\n{question}\n"
        inputs:
          - question
        outputs:
          - formatted_prompt

      - id: llm_step
        type: LLMInference
        model: gpt-4
        inputs:
          - formatted_prompt
        outputs:
          - answer
```

**What this means:**

- `steps:` - The actual processing instructions
- **Step 1: PromptTemplate** - Formats your question into a proper prompt
  - `template:` - Text with placeholders like `{question}`
  - Takes the user's `question` and creates `formatted_prompt`
- **Step 2: LLMInference** - Sends the prompt to the AI
  - `model: gpt-4` - Use the model we defined earlier
  - Takes `formatted_prompt` and returns `answer`

**Why two steps?** Separating prompt formatting from AI inference makes your app more maintainable and testable.

**Check your work:**

1. Validate: `qtype validate 01_hello_world.qtype.yaml`
2. Should still pass ✅

---

## Part 3: Run Your Application (5 minutes)

### Set Up Authentication

Create a file called `.env` in the same folder:

```
OPENAI_KEY=sk-your-key-here
```

Replace `sk-your-key-here` with your actual OpenAI API key.

---

### Test It!

Run your application:

```bash
qtype run -i '{"question":"What is 2+2?"}' 01_hello_world.qtype.yaml
```

**What you should see:**
```json
{
  "answer": "2+2 equals 4."
}
```

**Troubleshooting:**

- **"Authentication error"** → Check your API key in `.env`
- **"Model not found"** → Verify you have access to the model
- **"Variable not found"** → Check your indentation in the YAML file

---

### Try It With Different Questions

```bash
# Simple math
qtype run -i '{"question":"What is the capital of France?"}' 01_hello_world.qtype.yaml

# More complex
qtype run -i '{"question":"Explain photosynthesis in one sentence"}' 01_hello_world.qtype.yaml
```

---

## What You've Learned

Congratulations! You've learned:

✅ **Application structure** - Every QType app has an `id`  
✅ **Models** - How to configure AI providers  
✅ **Flows** - Where processing logic lives  
✅ **Variables** - How data moves through your app  
✅ **Steps** - Individual processing units (PromptTemplate, LLMInference)  
✅ **Validation** - How to check your work before running  

---

## Next Steps

**Reference the complete example:**

- [`01_hello_world.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/tutorials/01_hello_world.qtype.yaml) - Full working example

**Learn more:**

- [Application Concept](../Concepts/Core/application.md) - Full specification
- [All Step Types](../Concepts/Steps/index.md) - What else can you build?

---

## Common Questions

**Q: Why do I need to declare variables?**  
A: It makes data flow explicit and helps QType validate your app before running it.

**Q: Can I use multiple models in one app?**  
A: Yes! Define multiple models in the `models:` section and reference them by their `id` in steps.

**Q: My validation passed but I get errors when running. Why?**  
A: Validation checks structure, but runtime errors often involve authentication or model access. Check your API keys and model permissions.
