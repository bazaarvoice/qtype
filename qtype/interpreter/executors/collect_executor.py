from typing import Any, AsyncIterator

from qtype.interpreter.base.batch_step_executor import BatchedStepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Collect


def _find_common_ancestors(messages: list[FlowMessage]) -> dict[str, Any]:
    if not messages:
        return {}

    # 1. Start with all variables from the first message
    common_vars = messages[0].variables.copy()

    for msg in messages[1:]:
        # 2. Identify keys that either don't exist in this message
        #    OR have a different value (diverged)
        diverged_keys = [
            k
            for k, v in common_vars.items()
            if k not in msg.variables or msg.variables[k] != v
        ]
        # 3. Remove diverged keys to leave only the "Common Ancestors"
        for k in diverged_keys:
            common_vars.pop(k)

    return common_vars


class CollectExecutor(BatchedStepExecutor):
    """Executor for Collect steps."""

    def __init__(
        self,
        step: Collect,
        context: ExecutorContext,
        **dependencies,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Collect):
            raise ValueError("CollectExecutor can only execute Collect steps.")
        self.step = step

    async def process_batch(
        self,
        batch: list[FlowMessage],
    ) -> AsyncIterator[FlowMessage]:
        """Process a batch of FlowMessages for the Collect step.

        Args:
            batch: A list of FlowMessages to process.

        Yields:
            FlowMessages with the results of processing.
        """

        # Note that the batch processor accumulates the messages that we need,
        # so this function isn't called until collection is ready.

        # outputs[0] and inputs[0] is safe here since semantic validation ensures only one output
        output_name = self.step.outputs[0].id
        input_name = self.step.inputs[0].id

        if len(batch) == 0:
            # No messages to process -- yield nothing
            return

        results = []
        for msg in batch:
            results.append(msg.variables[input_name])

        # Only variables common to all input messages are propagated at the end
        common_ancestors = _find_common_ancestors(batch)
        new_variables = {output_name: results} | common_ancestors
        yield FlowMessage(session=batch[0].session, variables=new_variables)
