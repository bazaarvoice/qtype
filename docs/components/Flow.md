### Flow

Defines a flow of steps that can be executed in sequence or parallel.
If input or output variables are not specified, they are inferred from
the first and last step, respectively.

- **description** (`str | None`): Optional description of the flow.
- **cardinality** (`StepCardinality`): The cardinality of the flow, inferred from its steps when set to 'auto'.
- **mode** (`Literal`): (No documentation available.)
- **steps** (`list[StepType | str]`): List of steps or step IDs.
