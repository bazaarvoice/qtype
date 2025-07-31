# Condition

Condition is a step that provides conditional branching logic within flows. It evaluates input values against specified conditions and routes execution to different steps based on the results, enabling dynamic workflow paths and decision-making capabilities.

Condition steps allow flows to adapt their behavior based on runtime data, user inputs, or processing results, making applications more intelligent and responsive to different scenarios.

## Rules and Behaviors

- **Required Input**: Condition steps must have exactly one input variable that provides the value to evaluate.
- **Required Then Step**: The `then` field is mandatory and specifies which step to execute when the condition is true.
- **Optional Else Step**: The `else` field specifies an alternative step to execute when the condition is false.
- **Equality Comparison**: Currently supports equality comparison through the `equals` field.
- **Step References**: Both `then` and `else` can reference steps by ID string or embed step definitions inline.
- **No Direct Outputs**: Condition steps don't produce direct outputs - their behavior determines which subsequent step executes.

--8<-- "components/Condition.md"

## Example Usage
