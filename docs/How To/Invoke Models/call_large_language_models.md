# Call Large Language Models

Send text input to an LLM and receive a response using the `LLMInference` step with a system message and configurable model parameters like temperature and max_tokens.

### QType YAML

```yaml
models:
  - type: Model
    id: nova_lite
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 500

steps:
  - type: LLMInference
    id: assistant
    model: nova_lite
    system_message: "You are a helpful assistant"
    inputs: [text]
    outputs: [response]
```

### Explanation

- **model**: Reference to a Model resource defining the LLM provider and model ID
- **inference_params**: Configuration for model behavior (temperature, max_tokens, top_p, etc.)
- **temperature**: Controls randomness (0.0 = deterministic, 1.0 = creative)
- **max_tokens**: Maximum number of tokens in the response
- **system_message**: Sets the assistant's persona and instructions for all requests
- **inputs**: Variables containing the user's text input to the LLM
- **outputs**: Variables where the LLM's response will be stored (must be type `text` or `ChatMessage`)

## Complete Example

```yaml
--8<-- "../examples/invoke_models/simple_llm_call.qtype.yaml"
```

Run with:
```bash
qtype run simple_llm_call.qtype.yaml --input '{"text": "What is the capital of France?"}'
```

## See Also

- [LLMInference Reference](../../components/LLMInference.md)
- [Model Reference](../../components/Model.md)
- [Tutorial: Conversational Chatbot](../../Tutorials/02-conversational-chatbot.md)
