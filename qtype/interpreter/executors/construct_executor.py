from typing import AsyncIterator

from qtype.dsl.model import ListType
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.interpreter.typing import instantiate_variable
from qtype.semantic.model import Construct


class ConstructExecutor(StepExecutor):
    """Executor for Construct steps."""

    def __init__(
        self,
        step: Construct,
        context: ExecutorContext,
        **dependencies,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Construct):
            raise ValueError(
                "ConstructExecutor can only execute Construct steps."
            )
        self.step = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a FlowMessage for the Construct step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessages with the results of processing.
        """
        try:
            # Safe since semantic validation ensures exactly one output variable
            output_var = self.step.outputs[0]

            if (
                isinstance(output_var.type, ListType)
                or len(self.step.inputs) == 1
            ):
                inputs = message.variables[self.step.inputs[0].id]
            elif hasattr(output_var.type, "model_validate"):
                # This is a custom type (Pydantic model)
                # field_bindings maps type field names to Variables
                inputs = {
                    field_name: message.variables[var.id]
                    for field_name, var in self.step.field_bindings.items()
                }
            else:
                raise ValueError(
                    "Construct step must have either a single input or output of a custom type."
                )
            constructed_value = instantiate_variable(output_var, inputs)
            yield message.copy_with_variables(
                {output_var.id: constructed_value}
            )
        except Exception as e:
            yield message.copy_with_error(self.step.id, e)
