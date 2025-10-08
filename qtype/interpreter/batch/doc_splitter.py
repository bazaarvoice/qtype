from __future__ import annotations

from typing import Any

import pandas as pd

from qtype.dsl.domain_types import RAGChunk, RAGDocument
from qtype.interpreter.batch.types import BatchConfig
from qtype.interpreter.conversions import to_text_splitter
from qtype.semantic.model import DocumentSplitter


def execute_document_splitter(
    splitter: DocumentSplitter,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute a DocumentSplitter for batch processing.

    Args:
        splitter: The DocumentSplitter step to execute.
        inputs: DataFrame of input rows to process.
        batch_config: Batch processing configuration.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple of (success_df, error_df) where:
        - success_df contains rows with chunks successfully created
        - error_df contains rows that failed with error information
    """
    success_rows = []
    error_rows = []

    # Get the input and output column names
    if len(splitter.inputs) != 1 or len(splitter.outputs) != 1:
        raise ValueError(
            "DocumentSplitter must have exactly one input and one output"
        )
    input_col = splitter.inputs[0].id
    output_col = splitter.outputs[0].id

    # Get the LlamaIndex text splitter
    llama_splitter = to_text_splitter(splitter)

    # Process each row
    for _, row in inputs.iterrows():
        row_dict = row.to_dict()
        try:
            # Get the document from the input column
            document: RAGDocument = row_dict[input_col]

            # Convert content to text if needed
            if isinstance(document.content, bytes):
                # Decode bytes to string
                content_text = document.content.decode("utf-8")
            elif isinstance(document.content, str):
                content_text = document.content
            else:
                raise ValueError(
                    f"Unsupported document content type: {type(document.content)}"
                )

            # Split the document using the LlamaIndex splitter
            # get_nodes_from_documents expects a list of LlamaIndex Document objects
            from llama_index.core.schema import Document as LlamaDocument

            llama_doc = LlamaDocument(
                text=content_text,
                metadata=document.metadata or {},
                id_=document.file_id,
            )
            nodes = llama_splitter.get_nodes_from_documents([llama_doc])

            # Create a RAGChunk for each node, repeating the input row data
            for node in nodes:
                chunk = RAGChunk(
                    content=node.text,
                    chunk_id=node.node_id,
                    document_id=document.file_id,
                    embedding=None,  # Embedding will be added later
                    metadata={
                        **(document.metadata or {}),
                        **(node.metadata or {}),
                    },
                )

                output_row = row_dict.copy()
                output_row[output_col] = chunk
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
