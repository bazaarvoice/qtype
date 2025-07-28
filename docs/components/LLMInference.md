# LLMInference

Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response.

## Members
- **memory** (`Memory | str | None`): Memory object to retain context across interactions.
- **model** (`ModelType | str`): The model to use for inference.
- **system_message** (`str | None`): Optional system message to set the context for the model.

---
