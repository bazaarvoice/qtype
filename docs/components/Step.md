### Step

Base class for components that take inputs and produce outputs.

- **id** (`str`): Unique ID of this component.
- **cardinality** (`StepCardinality`): Does this step emit 1 (one) or 0...N (many) instances of the outputs?
- **inputs** (`list[Variable | str] | None`): Input variables required by this step.
- **outputs** (`list[Variable | str] | None`): Variable where output is stored.
