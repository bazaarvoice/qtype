from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Explode


class ExplodeExecutor(StepExecutor):
    """Executor for Explode steps."""

    def __init__(
        self,
        step: Explode,
        context: ExecutorContext,
        **dependencies,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Explode):
            raise ValueError("ExplodeExecutor can only execute Explode steps.")
        self.step = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a FlowMessage for the Explode step.

        Args:
            message: A FlowMessage to process.
        Yields:
            FlowMessages with the results of processing.
        """
        try:
            input_name = self.step.inputs[0].id
            output_name = self.step.outputs[0].id

            input_value = message.variables.get(input_name)

            if not isinstance(input_value, list):
                raise ValueError(
                    f"Explode step expected a list for input '{input_name}', "
                    f"but got: {type(input_value).__name__}"
                )

            for item in input_value:
                yield message.copy_with_variables({output_name: item})
        except Exception as e:
            yield message.copy_with_error(self.step.id, e)
