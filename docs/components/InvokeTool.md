### InvokeTool

Invokes a tool with input and output bindings.

- **type** (`Literal`): (No documentation available.)
- **tool** (`Reference[ToolType] | str`): Tool to invoke.
- **input_bindings** (`dict[str, Reference[Variable] | str]`): Mapping from tool parameter names to flow variable names.
- **output_bindings** (`dict[str, Reference[Variable] | str]`): Mapping from tool output names to flow variable names.
