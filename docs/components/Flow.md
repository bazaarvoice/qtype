### Flow

Defines a flow of steps that can be executed in sequence or parallel.
If input or output variables are not specified, they are inferred from
the first and last step, respectively.

- **id** (`str`): Unique ID of the flow.
- **type** (`Literal`): (No documentation available.)
- **description** (`str | None`): Optional description of the flow.
- **steps** (`list[StepType | Reference[StepType]]`): List of steps or references to steps
- **interface** (`FlowInterface | None`): (No documentation available.)
- **variables** (`list[Variable]`): List of variables available at the application scope.
- **inputs** (`list[Reference[Variable] | str]`): Input variables required by this step.
- **outputs** (`list[Reference[Variable] | str]`): Resulting variables
