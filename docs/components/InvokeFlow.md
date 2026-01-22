### InvokeFlow

Invokes a flow with input and output bindings.

- **type** (`Literal`): (No documentation available.)
- **flow** (`Reference[Flow] | str`): Flow to invoke.
- **input_bindings** (`dict[str, Reference[Variable] | str]`): Mapping from flow input variable IDs to step variable names.
- **output_bindings** (`dict[str, Reference[Variable] | str]`): Mapping from flow output variable IDs to step variable names.
