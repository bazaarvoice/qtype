from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

import fsspec
import pandas as pd

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
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
        output_columns = {output.id for output in self.step.outputs}

        # get the path
        if isinstance(self.step.path, ConstantPath):
            file_path = self.step.path
        else:
            file_path = message.variables.get(self.step.path.id)
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

        # Determine file format from extension
        file_path_str = (
            file_path.uri if isinstance(file_path, ConstantPath) else file_path
        )
        extension = Path(file_path_str).suffix.lower()

        # Use fsspec to open the file and read with pandas
        with fsspec.open(file_path_str, "rb") as file_handle:
            if extension == ".csv":
                df = pd.read_csv(file_handle)  # type: ignore[arg-type]
            elif extension == ".parquet":
                df = pd.read_parquet(file_handle)  # type: ignore[arg-type]
            elif extension == ".json":
                df = pd.read_json(file_handle)  # type: ignore[arg-type]
            elif extension == ".jsonl":
                df = pd.read_json(
                    file_handle,
                    lines=True,  # type: ignore[arg-type]
                )
            else:
                # Default to parquet if no extension or unknown
                df = pd.read_parquet(file_handle)  # type: ignore[arg-type]

        # confirm the outputs exist in the dataframe
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

        for row in df.to_dict(orient="records"):
            # Filter to only the expected output columns if they exist
            row = {
                str(k): v for k, v in row.items() if str(k) in output_columns
            }
            yield message.copy_with_variables(new_variables=row)
        await self.stream_emitter.status(
            f"Emitted {len(df)} rows from: {file_path_str}"
        )
