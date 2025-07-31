### Step

Base class for components that take inputs and produce outputs.

- **id** (`str`): Unique ID of this component.
- **inputs** (`list[Variable | str] | None`): Input variables required by this step.
- **outputs** (`list[Variable | str] | None`): Variable where output is stored.
