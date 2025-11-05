from itertools import groupby
from typing import AsyncIterator

import fsspec
import pandas as pd

from qtype.interpreter.base.batch_step_executor import BatchedStepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import ConstantPath, FileWriter, Variable


class FileWriterExecutor(BatchedStepExecutor):
    """Executor for FileWriter steps."""

    def __init__(
        self,
        step: FileWriter,
        context: ExecutorContext,
        **dependencies,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, FileWriter):
            raise ValueError(
                "FileWriterExecutor can only execute FileWriter steps."
            )
        self.step = step

    def to_pandas(self, messages: list[FlowMessage]) -> pd.DataFrame:
        """Convert a list of FlowMessages to a pandas DataFrame."""
        records = [msg.variables for msg in messages]
        return pd.DataFrame.from_records(records)

    async def process_batch(
        self,
        batch: list[FlowMessage],
    ) -> AsyncIterator[FlowMessage]:
        """Process a batch of FlowMessages for the FileWriter step.

        Args:
            batch: A list of FlowMessages to process.

        Yields:
            FlowMessages with the results of processing.
        """
        output_name = None
        if len(self.step.outputs):
            output_name = self.step.outputs[0].id

        if isinstance(self.step.path, ConstantPath):
            file_path = self.step.path.uri
            df = self.to_pandas(batch)
            # A fixed path is provided -- just write all of the data
            await self.stream_emitter.status(
                f"Writing {len(df)} records to {file_path}"
            )
            with fsspec.open(file_path, "wb") as file_handle:
                df.to_parquet(file_handle, index=False)  # type: ignore[arg-type]
            await self.stream_emitter.status(
                f"Wrote {len(df)} records to {file_path}"
            )
            for msg in batch:
                yield (
                    msg
                    if not output_name
                    else msg.copy_with_variables({output_name: file_path})
                )
        else:
            # Group messages by file path (path is a Variable in this branch)
            if not isinstance(self.step.path, Variable):
                raise ValueError(
                    "Expected path to be a Variable in dynamic path case."
                )

            path_var_id = self.step.path.id

            # Sort messages by file path for groupby
            sorted_batch = sorted(
                batch, key=lambda msg: msg.variables[path_var_id]
            )

            # Group messages by file path
            grouped_messages = groupby(
                sorted_batch, key=lambda msg: msg.variables[path_var_id]
            )

            distinct_paths = list(
                set(msg.variables[path_var_id] for msg in batch)
            )
            await self.stream_emitter.status(
                f"There are {len(distinct_paths)} different files to write."
            )
            for file_path, msg_group in grouped_messages:
                msg_list = list(msg_group)
                df_group = self.to_pandas(msg_list)
                await self.stream_emitter.status(
                    f"Writing {len(df_group)} records to {file_path}"
                )
                with fsspec.open(file_path, "wb") as file_handle:
                    df_group.to_parquet(file_handle, index=False)  # type: ignore[arg-type]
                await self.stream_emitter.status(
                    f"Wrote {len(df_group)} records to {file_path}"
                )
                # Re-yield the original messages for this group
                for msg in batch:
                    yield (
                        msg
                        if not output_name
                        else msg.copy_with_variables({output_name: file_path})
                    )
