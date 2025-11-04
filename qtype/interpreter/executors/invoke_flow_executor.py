from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import InvokeFlow


class InvokeFlowExecutor(StepExecutor):
    """Executor for InvokeFlow steps."""

    def __init__(
        self, step: InvokeFlow, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, InvokeFlow):
            raise ValueError(
                ("InvokeFlowExecutor can only execute InvokeFlow steps.")
            )
        self.step: InvokeFlow = step

    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the InvokeFlow step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessage with results from the invoked flow.
        """
        from qtype.interpreter.flow import run_flow

        initial = message.copy_with_variables(
            {
                id: message.variables.get(var.id)
                for var, id in self.step.input_bindings.items()
            }
        )
        # Pass through context (already available as self.context)
        result = await run_flow(
            self.step.flow, [initial], context=self.context
        )

        for msg in result:
            yield msg.copy_with_variables(
                {
                    var.id: msg.variables.get(id)
                    for var, id in self.step.output_bindings.items()
                }
            )
