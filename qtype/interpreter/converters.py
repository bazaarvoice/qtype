"""Converters between DataFrames and FlowMessages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fsspec
import pandas as pd
from pydantic import BaseModel

from qtype.interpreter.types import FlowMessage, Session
from qtype.interpreter.typing import convert_dict_to_typed_variables
from qtype.semantic.model import Flow, Variable


def flow_messages_to_dataframe(
    messages: list[FlowMessage], flow: Flow
) -> pd.DataFrame:
    """
    Convert a list of FlowMessages to a DataFrame.

    Extracts output variables from each message based on the flow's outputs.

    Args:
        messages: List of FlowMessages with results
        flow: Flow definition containing output variable specifications

    Returns:
        DataFrame with one row per message, columns for each output variable
    """
    results = []
    for idx, message in enumerate(messages):
        row_data: dict[str, Any] = {"row": idx}

        # Extract output variables
        for var in flow.outputs:
            if var.id in message.variables:
                value = message.variables[var.id]
                if isinstance(value, BaseModel):
                    value = value.model_dump()
                row_data[var.id] = value
            else:
                row_data[var.id] = None

        # Include error if present
        if message.is_failed():
            row_data["error"] = (
                message.error.error_message
                if message.error
                else "Unknown error"
            )
        else:
            row_data["error"] = None

        results.append(row_data)

    return pd.DataFrame(results)


def read_dataframe_from_file(
    file_path: str,
) -> pd.DataFrame:
    """
    Read a file into a pandas DataFrame.

    Automatically detects file format based on MIME type and supports both
    local and remote files via fsspec. Returns raw DataFrame without type
    conversion.

    Args:
        file_path: Path to the file (local or remote, e.g., s3://bucket/file)

    Returns:
        DataFrame with data from the file

    Raises:
        ValueError: If file format is not supported or mime type detection fails
        FileNotFoundError: If file does not exist

    Supported formats:
        - CSV (.csv)
        - JSON (.json)
        - JSONL (.jsonl, JSON Lines)
        - Parquet (.parquet)
        - Excel (.xlsx, .xls)

    Examples:
        >>> # Read CSV
        >>> df = read_dataframe_from_file("data.csv")
        >>>
        >>> # Read from S3
        >>> df = read_dataframe_from_file("s3://bucket/data.parquet")
    """
    import magic

    ext_to_mime = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".jsonl": "application/jsonlines",
        ".parquet": "application/vnd.parquet",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
    }
    # Detect MIME type - handle both local and remote files
    # For remote files, we'll need to download a sample first
    if file_path.startswith(("http://", "https://", "s3://", "gs://")):
        # For remote files, infer from extension as fallback
        extension = Path(file_path).suffix.lower()
        # Map extensions to mime types
        mime_type = ext_to_mime.get(extension, "application/octet-stream")
    else:
        # Local file - use magic to detect mime type
        try:
            mime_type = magic.Magic(mime=True).from_file(file_path)
        except Exception as e:
            # Fallback to extension-based detection
            extension = Path(file_path).suffix.lower()
            mime_type = ext_to_mime.get(extension, "application/octet-stream")
            if mime_type == "application/octet-stream":
                raise ValueError(
                    f"Could not determine file type for {file_path}: {e}"
                )

    # Open file with fsspec (supports local and remote files)
    with fsspec.open(file_path, "rb") as file_handle:
        # Read based on MIME type
        if mime_type == "text/csv" or mime_type == "text/plain":
            df = pd.read_csv(file_handle)  # type: ignore[arg-type]
        elif mime_type in ["application/json", "application/jsonlines"]:
            # Check if it's JSONL by extension
            if Path(file_path).suffix.lower() == ".jsonl":
                df = pd.read_json(
                    file_handle,  # type: ignore[arg-type]
                    lines=True,
                )
            else:
                df = pd.read_json(file_handle)  # type: ignore[arg-type]
        elif mime_type in [
            "application/vnd.parquet",
            "application/octet-stream",
        ]:
            # Parquet is often detected as octet-stream
            df = pd.read_parquet(file_handle)  # type: ignore[arg-type]
        elif mime_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ]:
            df = pd.read_excel(file_handle)  # type: ignore[arg-type]
        else:
            raise ValueError(
                f"Unsupported MIME type for file {file_path}: {mime_type}"
            )

    return df


def dataframe_to_flow_messages(
    df: pd.DataFrame,
    variables: list[Variable],
    session: Session = Session(session_id="default"),
) -> list[FlowMessage]:
    """
    Convert a DataFrame to FlowMessages with type conversion.

    Each row in the DataFrame becomes a FlowMessage with variables converted
    to their proper types based on the Variable definitions.

    Args:
        df: DataFrame with raw data
        variables: List of Variable definitions for type conversion
        session: Session to use for all FlowMessages (default: Session(session_id="default"))

    Returns:
        List of FlowMessages, one per row, with typed variables

    Examples:
        >>> from qtype.semantic.model import Variable
        >>> from qtype.base.types import PrimitiveTypeEnum
        >>> import pandas as pd
        >>>
        >>> df = pd.DataFrame({"age": ["30"], "score": ["95.5"]})
        >>> vars = [
        ...     Variable(id="age", type=PrimitiveTypeEnum.int),
        ...     Variable(id="score", type=PrimitiveTypeEnum.float),
        ... ]
        >>> messages = dataframe_to_flow_messages(df, vars)
    """
    messages = []

    for row_dict in df.to_dict(orient="records"):
        typed_vars = convert_dict_to_typed_variables(row_dict, variables)
        messages.append(FlowMessage(session=session, variables=typed_vars))

    return messages
