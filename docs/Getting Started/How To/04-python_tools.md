# Create Tools from Python Modules

QType allows you to automatically convert Python functions into QType tools. This tutorial will walk you through creating a Python module with functions and converting them into a QType specification that can be used in your applications.

## Prerequisites

Before following this tutorial, make sure you understand:

- [Variables and types](../../Concepts/variable.md) in QType
- [Primitive types](../../components/PrimitiveTypeEnum.md) 
- [Domain types](./domain-types.md)
- [Custom types](./custom-types.md)

## Overview

The `qtype convert module` command analyzes Python functions in a module and automatically generates QType tool definitions. This saves you from manually writing tool specifications and ensures consistency between your Python code and QType definitions.

## Supported Types

For functions to be converted successfully, all arguments and return types must use supported type annotations:

### Primitive Types
- `str` → `text`
- `int` → `int` 
- `float` → `float`
- `bool` → `boolean`
- `bytes` → `file`
- `datetime.datetime` → `datetime`
- `datetime.date` → `date`
- `datetime.time` → `time`

### Domain Types
- `ChatMessage` from `qtype.dsl.domain_types`
- `ChatContent` from `qtype.dsl.domain_types`
- `Embedding` from `qtype.dsl.domain_types`

### Custom Types
You can use your own classes **only if** they inherit from `pydantic.BaseModel`. These will be automatically converted to QType custom types.

## Creating a Sample Module

Let's create a sample Python module with utility functions. Create a new file called `my_utilities.py`:

```python
from datetime import datetime, timedelta
from pydantic import BaseModel


class ProcessingResult(BaseModel):
    """Result of a text processing operation."""
    processed_text: str
    word_count: int
    processing_time: float


def count_words(text: str) -> int:
    """
    Count the number of words in a text string.
    
    Args:
        text: The input text to count words in.
        
    Returns:
        Number of words in the text.
    """
    return len(text.split())


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as a string.
    
    Args:
        timestamp: The datetime to format.
        format_str: The format string to use.
        
    Returns:
        Formatted datetime string.
    """
    return timestamp.strftime(format_str)


def calculate_future_date(start_date: datetime, days_ahead: int) -> datetime:
    """
    Calculate a future date by adding days to a start date.
    
    Args:
        start_date: The starting date.
        days_ahead: Number of days to add.
        
    Returns:
        The calculated future date.
    """
    return start_date + timedelta(days=days_ahead)


def process_text_advanced(text: str, uppercase: bool = False) -> ProcessingResult:
    """
    Process text and return detailed results.
    
    Args:
        text: The text to process.
        uppercase: Whether to convert to uppercase.
        
    Returns:
        Processing results including word count and timing.
    """
    import time
    start_time = time.time()
    
    processed = text.upper() if uppercase else text.lower()
    word_count = len(text.split())
    processing_time = time.time() - start_time
    
    return ProcessingResult(
        processed_text=processed,
        word_count=word_count,
        processing_time=processing_time
    )
```

## Converting the Module to QType Tools

Now convert your Python module to QType tools using the CLI:

```bash
qtype convert module my_utilities -o my_utilities.qtype.yml
```

This will generate a QType specification file with all your functions converted to tools.

## Understanding the Generated Output

The generated `my_utilities.qtype.yml` file will contain:

```yaml
description: Tools created from Python module my_utilities
id: my_utilities
tools:
- description: Count the number of words in a text string.
  function_name: count_words
  id: my_utilities.count_words
  inputs:
  - id: count_words.text
    type: text
  module_path: my_utilities
  name: count_words
  outputs:
  - id: my_utilities.count_words.result
    type: int

- description: Format a datetime object as a string.
  function_name: format_timestamp
  id: my_utilities.format_timestamp
  inputs:
  - id: format_timestamp.timestamp
    type: datetime
  - id: format_timestamp.format_str
    type: text
  module_path: my_utilities
  name: format_timestamp
  outputs:
  - id: my_utilities.format_timestamp.result
    type: text

- description: Calculate a future date by adding days to a start date.
  function_name: calculate_future_date
  id: my_utilities.calculate_future_date
  inputs:
  - id: calculate_future_date.start_date
    type: datetime
  - id: calculate_future_date.days_ahead
    type: int
  module_path: my_utilities
  name: calculate_future_date
  outputs:
  - id: my_utilities.calculate_future_date.result
    type: datetime

- description: Process text and return detailed results.
  function_name: process_text_advanced
  id: my_utilities.process_text_advanced
  inputs:
  - id: process_text_advanced.text
    type: text
  - id: process_text_advanced.uppercase
    type: boolean
  module_path: my_utilities
  name: process_text_advanced
  outputs:
  - id: my_utilities.process_text_advanced.result
    type: ProcessingResult

types:
- description: Result of a text processing operation.
  id: ProcessingResult
  properties:
    processed_text: str
    word_count: int
    processing_time: float
```

## Key Features of the Conversion

### Automatic Type Mapping
- Python types are automatically mapped to QType types
- Type hints are required for all function parameters and return values
- Docstrings are extracted and used as tool descriptions

### Custom Type Generation
- Pydantic models are automatically converted to QType custom types
- The `ProcessingResult` class becomes a custom type definition
- All fields in the Pydantic model are preserved with their types

### Tool Naming
- Tool IDs follow the pattern: `{module_path}.{function_name}`
- Input variable IDs follow: `{function_name}.{parameter_name}`
- Output variable IDs follow: `{module_path}.{function_name}.result`

## Requirements and Limitations

### Function Requirements
1. **Type Annotations**: All functions must have complete type annotations for parameters and return values
2. **Public Functions**: Only public functions (not starting with `_`) are converted
3. **Module Definition**: Functions must be defined in the target module (not imported from elsewhere)
4. **Supported Types**: All types must be mappable to QType types

### Unsupported Features
- Functions with `*args` or `**kwargs` parameters
- Functions without return type annotations
- Complex generic types (e.g., `Dict[str, List[int]]`)
- Circular type references

## Using Generated Tools

Once you have your `.qtype.yml` file, you can use these tools in QType applications:

```yaml
id: text_processing_app
name: Text Processing Application

tools:
  - import: my_utilities.qtype.yml

flows:
  - id: word_counter_flow
    name: Count Words Flow
    inputs:
      - id: input_text
        type: text
    steps:
      - id: count
        type: tool
        tool: my_utilities.count_words
        inputs:
          text: $input_text
    outputs:
      - id: word_count
        source: count.result
```

## Best Practices

### Function Design
1. **Clear Docstrings**: Write descriptive docstrings as they become tool descriptions
2. **Single Responsibility**: Keep functions focused on one task
3. **Type Safety**: Use precise type hints rather than `Any`
4. **Error Handling**: Include proper error handling in your functions

### Module Organization
1. **Logical Grouping**: Group related functions in the same module
2. **Dependencies**: Keep external dependencies minimal
3. **Testing**: Write tests for your functions before converting

### Custom Types
1. **Pydantic Models**: Use Pydantic BaseModel for complex return types
2. **Field Documentation**: Add docstrings to model fields
3. **Type Validation**: Leverage Pydantic's validation features

## Troubleshooting

### Common Issues

**"Function must have a return type annotation"**
- Ensure all functions have explicit return type annotations

**"Unsupported Python type"**
- Check that all parameter and return types are supported
- Consider using custom Pydantic models for complex types

**"No public functions found"**
- Verify functions don't start with underscore
- Check functions are defined in the target module

### Debugging Tips
1. Start with simple functions and gradually add complexity
2. Test your Python functions independently before conversion
3. Use `mypy` to validate type annotations before conversion

