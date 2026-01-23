### Variable

Schema for a variable that can serve as input, output, or parameter within the DSL.

- **id** (`str`): Unique ID of the variable. Referenced in prompts or steps.
- **type** (`VariableType | str`): Type of data expected or produced. Either a CustomType or domain specific type.
- **optional** (`bool`): Whether this variable can be unset or None. Use '?' suffix in type string as shorthand (e.g., 'text?').
- **ui** (`TextInputUI | FileUploadUI | None`): Hints for the UI if needed.
