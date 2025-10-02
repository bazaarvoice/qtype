# Observe with Telemetry

QType supports telemetry for all applications out of the box -- simply add the [Telemetry](Concepts/telemetry.md) field to your application.

In this tutorial, we'll demonstrate how to add telemetry and use [Arize Phoenix](https://phoenix.arize.com/) to analyze and understand the commiication with LLMs.

## Setting up Phoenix
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

## Adding Telemetry

Next, we'll add telemetry to the [Chatbot Example](./chatbot-example.md) qtype definition:
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

Notice the `telemetry` field is set to your local phoenix installation.

Next, navigate to `http://localhost:8000/ui` and have a quick conversation

## Viewing Traces

Now, you can navigate to [http://localhost:6006](http://localhost:6006). You'll see a project who's name matches your application id:

![Phoenix Projects](./phoenix_projects.png)

Click on the project, and you'll see the traces of your conversation:

![Phoenix Projects](./phoenix_traces.png)


And that's it! Now you'll have a record of all of the calls to and from llms for your application.