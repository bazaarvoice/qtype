# A Simple Chatbot

This example creates a simple chat bot that you can converse with in the included UI, and keep track of the execution with open telemetry.

### The QType File

```yaml
--8<-- "../examples/chat_with_telemetry.qtype.yaml"
```

You can download it [here](https://github.com/bazaarvoice/qtype/blob/main/examples/chat_with_telemetry.qtype.yaml).
There is also a version for [AWS Bedrock](https://github.com/bazaarvoice/qtype/blob/main/examples/chat_with_telemetry_bedrock.qtype.yaml).

### The Architecture 

```mermaid
--8<-- "Examples/chat_with_telemetry.mmd"
```

### Authorization

You'll need an OpenAI key.
Put it in a `.env` file, and name the variable `OPENAI_KEY`

### Telemetry
The code pushes telemetry to a sync on your local machine. Start `arize-phoenix` with:
```bash
phoenix serve
```
Before running.

### Runing the App

Just run:
```bash
qtype serve chat_with_telemetry.qtype.yaml
```

And you can opne thet chat at [http://localhost:8000/ui](http://localhost:8000/ui)