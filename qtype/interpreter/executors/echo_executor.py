from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Echo


class EchoExecutor(StepExecutor):
    """Executor for Echo steps.

    Passes through input variables as outputs without modification.
    Useful for debugging flows by inspecting variable values at specific
    points in the execution pipeline.
    """

    def __init__(
        self,
        step: Echo,
        context: ExecutorContext,
        **dependencies: object,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Echo):
            raise ValueError("EchoExecutor can only execute Echo steps.")
        self.step: Echo = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the Echo step.

        Reads all input variables from the message and copies them to
        the output variables with the same IDs.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage with the echoed variables.
        """
        try:
            # Build a dict of output variable values by reading from inputs
            output_vars = {}
            for input_var in self.step.inputs:
                value = message.variables.get(input_var.id)
                # Find the corresponding output variable ID (should match)
                for output_var in self.step.outputs:
                    if output_var.id == input_var.id:
                        output_vars[output_var.id] = value
                        break

            await self.stream_emitter.status(
                f"Echoed {len(output_vars)} variable(s) in step {self.step.id}",
            )
            yield message.copy_with_variables(output_vars)

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
