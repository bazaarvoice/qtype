### FieldExtractor

Extracts specific fields from input data using JSONPath expressions.
This step uses JSONPath syntax to extract data from structured inputs
(Pydantic models, dicts, lists). The input is first converted to a dict
using model_dump() if it's a Pydantic model, then the JSONPath expression
is evaluated.
If the JSONPath matches multiple values, the step yields multiple output
messages (1-to-many cardinality). If it matches a single value, it yields
one output message. If it matches nothing, it raises an error.
The extracted data is used to construct the output variable by passing it
as keyword arguments to the output type's constructor.
If there is no match and the output variable is optional, it is set to None.
If there is no match and the output variable is required, an error is raised.
Example JSONPath expressions:
- `$.field_name` - Extract a single field
- `$.items[*]` - Extract all items from a list
- `$.items[?(@.price > 10)]` - Filter items by condition

- **type** (`Literal`): (No documentation available.)
- **json_path** (`str`): JSONPath expression to extract data from the input. Uses jsonpath-ng syntax.
