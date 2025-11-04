import string
from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import PromptTemplate


def get_format_arguments(format_string: str) -> set[str]:
    formatter = string.Formatter()
    arguments = []
    for literal_text, field_name, format_spec, conversion in formatter.parse(
        format_string
    ):
        if field_name:
            arguments.append(field_name)
    return set(arguments)


class PromptTemplateExecutor(StepExecutor):
    """Executor for PromptTemplate steps."""

    def __init__(
        self, step: PromptTemplate, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, PromptTemplate):
            raise ValueError(
                (
                    "PromptTemplateExecutor can only execute "
                    "PromptTemplate steps."
                )
            )
        self.step: PromptTemplate = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the PromptTemplate step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessage with the results of processing.
        """
        format_args = get_format_arguments(self.step.template)
        try:
            # Read input values from FlowMessage.variables
            input_map = {}
            for var in self.step.inputs:
                if var.id in format_args:
                    value = message.variables.get(var.id)
                    if value is not None:
                        input_map[var.id] = value

            missing = format_args - input_map.keys()
            if missing:
                raise ValueError(
                    (
                        "The following fields are in the prompt template "
                        f"but not in the inputs: {missing}"
                    )
                )
            result = self.step.template.format(**input_map)
            output_var_id = self.step.outputs[0].id

            await self.stream_emitter.status(
                (f"Processed message with PromptTemplate step {self.step.id}"),
            )
            yield message.copy_with_variables({output_var_id: result})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
