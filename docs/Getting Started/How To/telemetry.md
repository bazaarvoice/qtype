# Observe with Telemetry

QType supports telemetry for all applications out of the box -- simply add the [Telemetry](../../Concepts/telemetry.md) field to your application.

QType integrates with popular observability platforms to help you understand, debug, and optimize your LLM applications. This guide covers how to set up telemetry with Phoenix and Langfuse.

## Supported Providers

- **Phoenix** - Open-source LLM observability from Arize AI (default)
- **Langfuse** - Open-source LLM engineering platform with tracing and analytics

## Phoenix Integration

[Arize Phoenix](https://phoenix.arize.com/) is an open-source platform for LLM observability that runs locally or in the cloud.

### Setting up Phoenix
First, ensure you have installed the qtype `interpreter`:
```bash
pip install qtype[interpreter]
```

Next, install [Arize Phoenix](https://phoenix.arize.com/):
```bash
pip install arize-phoenix
```

and launch it:
```bash
phoenix serve
```

This launches Phoenix on your local machine and listens for trace data at `http://localhost:6006/v1/traces`.

### Adding Phoenix Telemetry

Add telemetry to your QType application:
```yaml

```yaml
id: hello_world
telemetry:
  id: hello_world_telemetry
  endpoint: http://localhost:6006/v1/traces
flows:
  - id: simple_chat_example
    description: A simple stateful chat flow with OpenAI
    mode: Chat
    steps:
      - id: llm_inference_step
        memory: 
          id: chat_memory
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
          - id: response_message
            type: ChatMessage
```

Notice the `telemetry` field with the Phoenix endpoint. The `provider` defaults to `"Phoenix"` so you don't need to specify it.

### Viewing Phoenix Traces

1. Start your application:
   ```bash
   qtype serve your-app.qtype.yaml
   ```

2. Navigate to `http://localhost:8000/ui` and have a conversation

3. View traces at [http://localhost:6006](http://localhost:6006). You'll see a project whose name matches your application id:

   ![Phoenix Projects](./phoenix_projects.png)

4. Click on the project to see the traces of your conversation:

   ![Phoenix Traces](./phoenix_traces.png)

Now you'll have a complete record of all LLM calls and interactions!

## Langfuse Integration

[Langfuse](https://langfuse.com) is an open-source LLM engineering platform that provides tracing, analytics, prompt management, and evaluation capabilities.

### Getting Langfuse Credentials

1. Sign up for [Langfuse Cloud](https://cloud.langfuse.com) or deploy self-hosted
2. Create a new project
3. Navigate to Settings → API Keys
4. Generate a new API key pair (public_key and secret_key)
5. Store credentials in environment variables:
   ```bash
   export LANGFUSE_PUBLIC_KEY="pk-lf-..."
   export LANGFUSE_SECRET_KEY="sk-lf-..."
   ```

### Adding Langfuse Telemetry

Configure Langfuse as your telemetry provider:

```yaml
telemetry:
  id: langfuse_telemetry
  provider: Langfuse
  endpoint: https://cloud.langfuse.com
  args:
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}
```

**Required fields:**
- **provider**: Must be set to `"Langfuse"`
- **endpoint**: Langfuse host URL
  - Cloud: `https://cloud.langfuse.com`
  - Self-hosted: Your instance URL
- **args.public_key**: Your Langfuse public key
- **args.secret_key**: Your Langfuse secret key

### Complete Langfuse Example

```yaml
id: hello_world_langfuse
description: A simple chat flow with Langfuse telemetry
models:
  - type: Model
    id: gpt4
    provider: openai
    model_id: gpt-4
    inference_params:
      temperature: 0.7
      max_tokens: 512
    auth: openai_auth
auths:
  - type: api_key
    id: openai_auth
    api_key: ${OPENAI_KEY}
memories:
  - id: chat_memory
    token_limit: 10000
flows:
  - type: Flow
    id: chat_example
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
        model: gpt4
        memory: chat_memory
        system_message: "You are a helpful assistant."
        inputs:
          - user_message
        outputs:
          - response
telemetry:
  id: langfuse_telemetry
  provider: Langfuse
  endpoint: https://cloud.langfuse.com
  args:
    public_key: ${LANGFUSE_PUBLIC_KEY}
    secret_key: ${LANGFUSE_SECRET_KEY}
```

### Viewing Langfuse Traces

1. Run your application:
   ```bash
   qtype serve examples/chat_with_langfuse.qtype.yaml
   ```

2. Interact with your application at http://localhost:8000/ui

3. View traces in Langfuse:
   - Go to https://cloud.langfuse.com
   - Navigate to your project
   - View traces in the Tracing tab

### How Langfuse Integration Works

QType integrates with Langfuse via OpenTelemetry's OTLP protocol:

1. Creates an OpenTelemetry TracerProvider with your project name as the service name
2. Configures an OTLP HTTP exporter that sends spans to Langfuse's `/api/public/otel` endpoint
3. Uses Basic Authentication with your public_key:secret_key credentials
4. Automatically instruments LlamaIndex to capture all LLM interactions

All LLM calls, steps, and flows are automatically traced and sent to Langfuse.

## Using AWS Secrets Manager

Both Phoenix and Langfuse support storing credentials in AWS Secrets Manager:

```yaml
secret_manager:
  type: aws
  region: us-east-1

telemetry:
  id: langfuse_telemetry
  provider: Langfuse
  endpoint: https://cloud.langfuse.com
  args:
    public_key:
      secret: langfuse-credentials
      key: public_key
    secret_key:
      secret: langfuse-credentials
      key: secret_key
```

## Troubleshooting

### No traces appearing

**Phoenix:**
- Verify Phoenix is running on the correct port (default: 6006)
- Check the endpoint URL in your telemetry configuration
- Ensure no firewall is blocking the connection

**Langfuse:**
- Verify your credentials are correct (public_key starts with `pk-lf-`, secret_key starts with `sk-lf-`)
- Check the endpoint URL (should NOT include `/api/public/otel` - this is added automatically)
- Ensure your Langfuse project exists
- Check application logs for authentication errors
- Verify no extra whitespace in credentials

### Self-hosted Langfuse

If using self-hosted Langfuse, set the endpoint to your instance URL:
```yaml
telemetry:
  provider: Langfuse
  endpoint: https://langfuse.yourcompany.com
```

## Learn More

- [Phoenix Documentation](https://phoenix.arize.com/)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse OpenTelemetry Integration](https://langfuse.com/docs/integrations/opentelemetry)
- [QType Telemetry Concepts](../../Concepts/telemetry.md)