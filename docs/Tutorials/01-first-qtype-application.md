# Tutorial: Build Your First QType Application

**What you'll learn:** In 15 minutes, you'll build a working AI-powered question-answering application and understand the core concepts of QType.

**What you'll build:** A simple app that takes a question, sends it to an AI model, and returns an answer.

## Before You Begin

Make sure you have:

- QType installed: `pip install qtype[interpreter]`
- Either an AWS Bedrock account OR an OpenAI API key
- A text editor
- 15 minutes

**Don't worry if:** You've never used YAML before - we'll explain everything as we go.

---

## Part 1: Your First QType File (5 minutes)

### Create the File

Create a new file called `my_first_app.qtype.yaml` and add:

```yaml
id: hello_world
description: My first QType application
```

**What this means:**

- Every QType application starts with an `id` - a unique name for your app
- The `description` helps you remember what the app does (optional but helpful)

**Check your work:** Your file should have exactly 2 lines. Save it.

---

### Add Your AI Model

Add these lines to your file:

```yaml
id: hello_world
description: My first QType application

models:

- type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo
    inference_params:
      temperature: 0.7
```

**What this means:**

- `models:` - Where you configure which AI to use
- `type: Model` - Tells QType "this is an AI model"
- `id: gpt-4` - A nickname you'll use to refer to this model
- `provider: openai` - Which AI service to use
- `temperature: 0.7` - Controls creativity (0 = focused, 1 = creative)

**Check your work:**

1. Make sure the indentation matches exactly (2 spaces for each level)
2. Save the file
3. Run: `qtype validate my_first_app.qtype.yaml`
4. You should see: `✅ Validation successful`

**Troubleshooting:** If you get an error about indentation, check that you're using spaces (not tabs) and that each nested item is indented by exactly 2 spaces.

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
  - `answer` - What the AI responds
- `inputs:` and `outputs:` - Which variables go in and out

**Check your work:**

1. Validate again: `qtype validate my_first_app.qtype.yaml`
2. Still should see: `✅ Validation successful`

---

### Add Processing Steps

Now tell QType what to do with the question. Add this inside your flow (after `outputs:`):

```yaml
    steps:

- id: llm_step
        type: LLMInference
        model: gpt-4
        system_message: "You are a helpful assistant."
        inputs:

- question
        outputs:

- answer
```

**What this means:**

- `steps:` - The actual processing instructions
- `type: LLMInference` - "Send this to an AI model"
- `model: gpt-4` - Use the model we defined earlier (by its `id`)
- `system_message:` - Instructions for the AI
- `inputs: [question]` - Give the AI the user's question
- `outputs: [answer]` - Put the AI's response in `answer`

**Check your work:**

1. Validate: `qtype validate my_first_app.qtype.yaml`
2. Should still pass ✅

---

## Part 3: Run Your Application (5 minutes)

### Set Up Authentication

Create a file called `.env` in the same folder:

```
OPENAI_API_KEY=sk-your-key-here
```

Replace `sk-your-key-here` with your actual OpenAI API key.

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

### Test It!

Run your application:

```bash
qtype run -i '{"question":"What is 2+2?"}' my_first_app.qtype.yaml
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
qtype run -i '{"question":"What is the capital of France?"}' my_first_app.qtype.yaml

# More complex
qtype run -i '{"question":"Explain photosynthesis in one sentence"}' my_first_app.qtype.yaml
```

**Experiment:** Try changing the `system_message` to "You are a pirate" and run it again. What happens?

---

## What You've Learned

Congratulations! You've learned:

✅ **Application structure** - Every QType app has an `id`  
✅ **Models** - How to configure AI providers  
✅ **Flows** - Where processing logic lives  
✅ **Variables** - How data moves through your app  
✅ **Steps** - Individual processing units  
✅ **Validation** - How to check your work before running  

---

## Next Steps

Now that you understand the basics:

1. **[Tutorial 2: Build a Conversational Chatbot](02-conversational-chatbot.md)** - Make your app remember previous messages

**Want to dive deeper?**

- [Application Concept](../Concepts/Core/application.md) - Full specification
- [All Step Types](../Concepts/Steps/index.md) - What else can you build?

---

## Complete Code

Here's your complete `my_first_app.qtype.yaml`:

```yaml
id: hello_world
description: My first QType application

models:

- type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo
    inference_params:
      temperature: 0.7

flows:

- type: Flow
    id: simple_example
    variables:

- id: question
        type: text
      - id: answer
        type: text
    inputs:

- question
    outputs:

- answer
    steps:

- id: llm_step
        type: LLMInference
        model: gpt-4
        system_message: "You are a helpful assistant."
        inputs:

- question
        outputs:

- answer
```

**Download:** You can find a similar example at [examples/hello_world.qtype.yaml](https://github.com/bazaarvoice/qtype/blob/main/examples/hello_world.qtype.yaml)

---

## Common Questions

**Q: Why do I need to declare variables?**  
A: It makes data flow explicit and helps QType validate your app before running it.

**Q: Can I use multiple models in one app?**  
A: Yes! Define multiple models in the `models:` section and reference them by their `id` in steps.

**Q: My validation passed but I get errors when running. Why?**  
A: Validation checks structure, but runtime errors often involve authentication or model access. Check your API keys and model permissions.