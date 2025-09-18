### Invoke

Invokes a tool with input and output bindings.

- **tool** (`ToolType | str`): Tool to invoke.
- **input_bindings** (`dict[str, str]`): Mapping from step input IDs to tool input parameter names.
- **output_bindings** (`dict[str, str]`): Mapping from tool output parameter names to step output IDs.
