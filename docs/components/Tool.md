### Tool

Base class for callable functions or external operations available to the model or as a step in a flow.

- **id** (`str`): Unique ID of this component.
- **name** (`str`): Name of the tool function.
- **description** (`str`): Description of what the tool does.
- **inputs** (`dict[str, ToolParameter] | None`): Input parameters required by this tool.
- **outputs** (`dict[str, ToolParameter] | None`): Output parameters produced by this tool.
