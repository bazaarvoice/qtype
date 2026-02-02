# Create Tools from Python Modules

Generate QType tool definitions automatically from Python functions using `qtype convert module`, which analyzes type hints and docstrings to create properly typed tools.

### Command

```bash
qtype convert module myapp.utils --output tools.qtype.yaml
```

### QType YAML

**Input Python module** (`myapp/utils.py`):
```python
from datetime import datetime

def calculate_age(birth_date: datetime, reference_date: datetime) -> int:
    """Calculate age in years between two dates.
    
    Args:
        birth_date: The birth date
        reference_date: The date to calculate age at
    
    Returns:
        Age in complete years
    """
    age = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age
```

**Generated tool YAML** (`tools.qtype.yaml`):
```yaml
id: myapp.utils
description: Tools created from Python module myapp.utils
tools:
  - id: myapp.utils.calculate_age
    description: Calculate age in years between two dates.
    type: PythonFunctionTool
    function_name: calculate_age
    module_path: myapp.utils
    name: calculate_age
    inputs:
      - id: birth_date
        type: datetime
      - id: reference_date
        type: datetime
    outputs:
      - id: calculate_age_result
        type: int
```

### Explanation

- **`convert module`**: CLI subcommand that converts Python modules to tool definitions
- **module path**: Dot-separated Python module (e.g., `myapp.utils`, `package.submodule`) - must be importable
- **`--output`**: Target YAML file path; omit to print to stdout
- **Type hints**: Required on all parameters and return values; converted to QType types (int, text, datetime, etc.)
- **Optional parameters**: Detected from default values (e.g., `name: str = "default"` becomes `optional: true`)
- **Docstrings**: First line becomes tool description; supports Google, NumPy, and reStructuredText formats
- **Public functions only**: Functions starting with `_` are skipped

### Using Generated Tools

```yaml
references:
  - !include tools.qtype.yaml

flows:
  - id: check_age
    steps:
      - type: InvokeTool
        id: calc
        tool: myapp.utils.calculate_age
        input_bindings:
          birth_date: dob
          reference_date: today
        output_bindings:
          result: age
```

## See Also

- [Tutorial: Tools and Function Calling](../../Tutorials/04-tools-and-function-calling.md)
- [Create Tools from OpenAPI Specifications](create_tools_from_openapi_specifications.md)
- [PythonFunctionTool Reference](../../components/PythonFunctionTool.md)
