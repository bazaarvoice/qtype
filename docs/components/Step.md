### Step

Base class for components that take inputs and produce outputs.

- **id** (`str`): Unique ID of this component.
- **type** (`str`): Type of the step component.
- **inputs** (`list[Reference[Variable] | str]`): References to the variables required by this step.
- **outputs** (`list[Reference[Variable] | str]`): References to the variables where output is stored.
