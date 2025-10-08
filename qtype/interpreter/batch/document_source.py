from __future__ import annotations

import importlib
from typing import Any

import pandas as pd

from qtype.dsl.domain_types import RAGDocument
from qtype.interpreter.batch.types import BatchConfig
from qtype.interpreter.conversions import from_llama_document
from qtype.semantic.model import DocumentSource


def _execute_document_source(
    source: DocumentSource,
    args: dict[str, Any],
) -> list[RAGDocument]:
    """Executes a DocumentSource step to generate RAGDocument instances.

    Args:
        source: The DocumentSource step to execute.
        args: Arguments for the DocumentSource.

    Returns:
        A list of RAGDocument instances.
    """
    # Parse the reader module path
    # Format: 'google.GoogleDocsReader' -> llama_index.readers.google.GoogleDocsReader
    full_module_path = f"llama_index.readers.{source.reader_module}"
    # get the class name
    class_name = full_module_path.split(".")[-1]

    # Dynamically import the reader module
    try:
        reader_module = importlib.import_module(full_module_path)
        reader_class = getattr(reader_module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Failed to import reader class '{class_name}' from '{full_module_path}': {e}"
        ) from e

    # Combine source.args with runtime args
    combined_args = {**source.args, **args}

    # Instantiate the reader with combined arguments
    loader = reader_class(**combined_args)

    # Load documents using the loader
    # Most readers have a load_data method that returns a list of LlamaIndex Documents
    if hasattr(loader, "load_data"):
        llama_documents = loader.load_data(**combined_args)
    else:
        raise AttributeError(
            f"Reader class '{class_name}' does not have a 'load_data' method"
        )

    # Convert LlamaIndex Documents to RAGDocuments
    rag_documents = [from_llama_document(doc) for doc in llama_documents]

    return rag_documents


def execute_document_source(
    source: DocumentSource,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute a DocumentSource for batch processing.

    Args:
        source: The DocumentSource step to execute.
        inputs: DataFrame of input rows to process.
        batch_config: Batch processing configuration.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple of (success_df, error_df) where:
        - success_df contains rows with documents successfully loaded
        - error_df contains rows that failed with error information
    """
    success_rows = []
    error_rows = []

    # Get the output column name from the source
    if len(source.outputs) != 1:
        raise ValueError("DocumentSource must have exactly one output")
    output_col = source.outputs[0].id

    # Handle empty inputs case
    if inputs.empty:
        # Call with empty dict
        try:
            documents = _execute_document_source(source, {})
            for doc in documents:
                success_rows.append({output_col: doc})
        except Exception as e:
            error_rows.append({"error": str(e)})
    else:
        # Process each row
        for _, row in inputs.iterrows():
            row_dict = row.to_dict()
            try:
                # Call execute_document_source with the row as args
                documents = _execute_document_source(source, row_dict)

                # Create a row for each document, repeating the input row data
                for doc in documents:
                    output_row = row_dict.copy()
                    output_row[output_col] = doc
                    success_rows.append(output_row)

            except Exception as e:
                # Add the row to errors with exception info
                error_row = row_dict.copy()
                error_row["error"] = str(e)
                error_rows.append(error_row)

    # Convert lists to DataFrames
    success_df = pd.DataFrame(success_rows) if success_rows else pd.DataFrame()
    error_df = pd.DataFrame(error_rows) if error_rows else pd.DataFrame()

    return success_df, error_df
