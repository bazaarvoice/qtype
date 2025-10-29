### InvokeFlow

Invokes a flow with input and output bindings.

- **type** (`Literal`): (No documentation available.)
- **flow** (`Reference[Flow] | str`): Flow to invoke.
- **input_bindings** (`dict[Reference[Variable], str]`): Mapping from variable references to flow input variable IDs.
- **output_bindings** (`dict[Reference[Variable], str]`): Mapping from variable references to flow output variable IDs.
