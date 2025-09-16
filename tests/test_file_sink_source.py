"""Unit tests for file sink and source execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from qtype.base.exceptions import InterpreterError
from qtype.interpreter.batch.file_sink_source import (
    execute_file_sink,
    execute_file_source,
)
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.semantic.model import FileSink, FileSource, Variable


@pytest.fixture
def batch_config():
    """Create a default batch config."""
    return BatchConfig(error_mode=ErrorMode.FAIL)


@pytest.fixture
def file_source():
    """Create a FileSource with path."""
    return FileSource(
        id="test-source",
        path="/test/path.parquet",
        cardinality="many",
        inputs=[],
        outputs=[],
    )


@pytest.fixture
def file_source_no_path():
    """Create a FileSource without path (uses input variable)."""
    return FileSource(
        id="test-source",
        path=None,
        cardinality="many",
        inputs=[],
        outputs=[],
    )


@pytest.fixture
def file_sink():
    """Create a FileSink with path."""
    return FileSink(
        id="test-sink",
        path="/test/output.parquet",
        cardinality="one",
        inputs=[],
        outputs=[Variable(id="test-sink-file-uri", type="text", value=None)],
    )


@pytest.fixture
def file_sink_no_path():
    """Create a FileSink without path (uses input variable)."""
    from qtype.semantic.model import Variable

    return FileSink(
        id="test-sink",
        path=None,
        cardinality="one",
        inputs=[
            Variable(id="path", type="text", value=None),
            Variable(id="data", type="text", value=None),
        ],
        outputs=[Variable(id="test-sink-file-uri", type="text", value=None)],
    )


class TestFileSource:
    """Test file source execution."""

    @patch("fsspec.open")
    @patch("pandas.read_parquet")
    def test_read_with_fixed_path(
        self, mock_read, mock_fsspec_open, file_source, batch_config
    ):
        """Test reading from a fixed path."""
        mock_file_handle = MagicMock()
        mock_fsspec_open.return_value.__enter__.return_value = mock_file_handle
        mock_read.return_value = pd.DataFrame([{"data": "test"}])

        inputs = pd.DataFrame([{"input": "value"}])
        results, errors = execute_file_source(
            file_source, inputs, batch_config
        )

        mock_fsspec_open.assert_called_once_with("/test/path.parquet", "rb")
        mock_read.assert_called_once_with(mock_file_handle)
        assert len(results) == 1
        assert len(errors) == 0

    @patch("fsspec.open")
    @patch("pandas.read_parquet")
    def test_read_with_variable_path(
        self, mock_read, mock_fsspec_open, file_source_no_path, batch_config
    ):
        """Test reading from variable path."""
        mock_file_handle = MagicMock()
        mock_fsspec_open.return_value.__enter__.return_value = mock_file_handle
        mock_read.return_value = pd.DataFrame([{"data": "test"}])

        inputs = pd.DataFrame([{"path": "/var/file.parquet"}])
        results, errors = execute_file_source(
            file_source_no_path, inputs, batch_config
        )

        mock_fsspec_open.assert_called_once_with("/var/file.parquet", "rb")
        mock_read.assert_called_once_with(mock_file_handle)
        assert len(results) == 1
        assert len(errors) == 0

    def test_missing_path_raises_error(
        self, file_source_no_path, batch_config
    ):
        """Test error when path cannot be determined."""
        inputs = pd.DataFrame([{"other": "value"}])

        with pytest.raises(InterpreterError, match="No path specified"):
            execute_file_source(file_source_no_path, inputs, batch_config)


class TestFileSink:
    """Test file sink execution."""

    @patch("fsspec.open")
    @patch("pandas.DataFrame.to_parquet")
    def test_write_single_path(
        self, mock_to_parquet, mock_fsspec_open, file_sink, batch_config
    ):
        """Test writing to a single path."""
        # Setup mock file handle
        mock_file_handle = MagicMock()
        mock_fsspec_open.return_value.__enter__.return_value = mock_file_handle

        inputs = pd.DataFrame([{"data": "test1"}, {"data": "test2"}])
        results, errors = execute_file_sink(file_sink, inputs, batch_config)

        mock_fsspec_open.assert_called_once_with("/test/output.parquet", "wb")
        mock_to_parquet.assert_called_once_with(mock_file_handle, index=False)
        assert len(results) == len(inputs)
        assert (
            results[file_sink.outputs[0].id].iloc[0] == "/test/output.parquet"
        )
        assert len(errors) == 0

    @patch("fsspec.open")
    @patch("pandas.DataFrame.to_parquet")
    def test_write_multiple_paths(
        self,
        mock_to_parquet,
        mock_fsspec_open,
        file_sink_no_path,
        batch_config,
    ):
        """Test writing to multiple paths (splits and recurses)."""
        mock_file_handle = MagicMock()
        mock_fsspec_open.return_value.__enter__.return_value = mock_file_handle

        inputs = pd.DataFrame(
            [
                {"path": "/file1.parquet", "data": "test1"},
                {"path": "/file2.parquet", "data": "test2"},
            ]
        )

        results, errors = execute_file_sink(
            file_sink_no_path, inputs, batch_config
        )

        # Should write to both files
        assert mock_fsspec_open.call_count == 2
        assert mock_to_parquet.call_count == 2
        assert len(results) == 2
        assert len(errors) == 0

    def test_missing_path_raises_error(self, batch_config):
        """Test error when path cannot be determined."""
        # Create a FileSink with no path and no path input variable
        from qtype.semantic.model import Variable

        file_sink_no_path_var = FileSink(
            id="test-sink",
            path=None,
            cardinality="one",
            inputs=[Variable(id="data", type="text", value=None)],
            outputs=[
                Variable(id="test-sink-file-uri", type="text", value=None)
            ],
        )

        inputs = pd.DataFrame([{"data": "test", "other": "value"}])

        with pytest.raises(InterpreterError, match="No path specified"):
            execute_file_sink(file_sink_no_path_var, inputs, batch_config)

    @patch("fsspec.open")
    @patch(
        "pandas.DataFrame.to_parquet", side_effect=Exception("Write failed")
    )
    def test_write_error_drop_mode(
        self, mock_to_parquet, mock_fsspec_open, file_sink, batch_config
    ):
        """Test error handling in DROP mode."""
        mock_file_handle = MagicMock()
        mock_fsspec_open.return_value.__enter__.return_value = mock_file_handle

        batch_config.error_mode = ErrorMode.DROP
        inputs = pd.DataFrame([{"data": "test"}])

        results, errors = execute_file_sink(file_sink, inputs, batch_config)

        assert len(results) == 0
        assert len(errors) == 1
        assert "Write failed" in errors.iloc[0]["error"]

    def test_write_only_input_columns(self, batch_config, tmp_path):
        """Test that only columns specified in step.inputs are written to file."""
        from qtype.semantic.model import Variable

        # Create a temporary parquet file path
        output_file = tmp_path / "output.parquet"

        # Create a FileSink with specific input columns
        file_sink_with_inputs = FileSink(
            id="test-sink",
            path=str(output_file),
            cardinality="one",
            inputs=[
                Variable(id="col1", type="text", value=None),
                Variable(id="col2", type="text", value=None),
            ],
            outputs=[
                Variable(id="test-sink-file-uri", type="text", value=None)
            ],
        )

        # Input DataFrame with extra column that should not be written
        inputs = pd.DataFrame(
            [
                {
                    "col1": "value1",
                    "col2": "value2",
                    "extra_col": "should_not_be_written",
                },
                {
                    "col1": "value3",
                    "col2": "value4",
                    "extra_col": "also_should_not_be_written",
                },
            ]
        )

        # Execute the file sink
        results, errors = execute_file_sink(
            file_sink_with_inputs, inputs, batch_config
        )

        # Verify successful execution
        assert len(results) == 2
        assert len(errors) == 0
        assert results.iloc[0]["test-sink-file-uri"] == str(output_file)

        # Verify the file was actually created
        assert output_file.exists()

        # Read back the parquet file and verify only specified columns were written
        written_df = pd.read_parquet(output_file)

        # Verify only the specified input columns were written
        assert list(written_df.columns) == ["col1", "col2"]
        assert "extra_col" not in written_df.columns

        # Verify the data content
        assert len(written_df) == 2
        assert written_df.iloc[0]["col1"] == "value1"
        assert written_df.iloc[0]["col2"] == "value2"
        assert written_df.iloc[1]["col1"] == "value3"
        assert written_df.iloc[1]["col2"] == "value4"
