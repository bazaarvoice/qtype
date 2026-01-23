from __future__ import annotations

from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.converters import (
    dataframe_to_flow_messages,
    read_dataframe_from_file,
)
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import ConstantPath, FileSource


class FileSourceExecutor(StepExecutor):
    """Executor for FileSource steps."""

    def __init__(
        self, step: FileSource, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, FileSource):
            raise ValueError(
                "FileSourceExecutor can only execute FileSource steps."
            )
        self.step = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the FileSource step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessages with the results of processing.
        """
        # get the path
        if isinstance(self.step.path, ConstantPath):  # type: ignore[attr-defined]
            file_path = self.step.path  # type: ignore[attr-defined]
        else:
            file_path = message.variables.get(self.step.path.id)  # type: ignore[attr-defined]
            if not file_path:
                raise ValueError(
                    (
                        f"FileSource step {self.step.id} requires a path "
                        "variable."
                    )
                )
            await self.stream_emitter.status(
                f"Reading file from path: {file_path}"
            )

        # Get file path as string
        file_path_str = (
            file_path.uri if isinstance(file_path, ConstantPath) else file_path
        )

        # Read file into DataFrame using helper function
        df = read_dataframe_from_file(file_path_str)

        # Validate that expected output columns are present
        output_columns = {output.id for output in self.step.outputs}
        columns = set(df.columns)
        missing_columns = output_columns - columns
        if missing_columns:
            raise ValueError(
                (
                    f"File {file_path_str} missing expected columns: "
                    f"{', '.join(missing_columns)}. Available columns: "
                    f"{', '.join(columns)}"
                )
            )

        # Convert DataFrame to FlowMessages with type conversion
        flow_messages = dataframe_to_flow_messages(
            df, self.step.outputs, session=message.session
        )

        # Yield each message
        for flow_message in flow_messages:
            yield flow_message

        await self.stream_emitter.status(
            f"Emitted {len(df)} rows from: {file_path_str}"
        )
