### Variable

Schema for a variable that can serve as input, output, or parameter within the DSL.

- **id** (`str`): Unique ID of the variable. Referenced in prompts or steps.
- **type** (`VariableType | str`): Type of data expected or produced. Either a TypeDefinition or domain specific type.
