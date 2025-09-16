"""Unit tests for file sink and source execution."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from qtype.base.exceptions import InterpreterError
from qtype.interpreter.batch.file_sink_source import (
    execute_file_sink,
    execute_file_source,
)
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.semantic.model import FileSink, FileSource


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
        outputs=[],
    )


@pytest.fixture
def file_sink_no_path():
    """Create a FileSink without path (uses input variable)."""
    return FileSink(
        id="test-sink",
        path=None,
        cardinality="one",
        inputs=[],
        outputs=[],
    )


class TestFileSource:
    """Test file source execution."""

    @patch("pandas.read_parquet")
    def test_read_with_fixed_path(self, mock_read, file_source, batch_config):
        """Test reading from a fixed path."""
        mock_data = pd.DataFrame([{"data": "test"}])
        mock_read.return_value = mock_data

        inputs = pd.DataFrame([{"input": "value"}])
        results, errors = execute_file_source(
            file_source, inputs, batch_config
        )

        mock_read.assert_called_once_with("/test/path.parquet")
        assert len(results) == 1
        assert len(errors) == 0

    @patch("pandas.read_parquet")
    def test_read_with_variable_path(
        self, mock_read, file_source_no_path, batch_config
    ):
        """Test reading from variable path."""
        mock_data = pd.DataFrame([{"data": "test"}])
        mock_read.return_value = mock_data

        inputs = pd.DataFrame([{"path": "/var/file.parquet"}])
        results, errors = execute_file_source(
            file_source_no_path, inputs, batch_config
        )

        mock_read.assert_called_once_with("/var/file.parquet")
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

    @patch("pandas.DataFrame.to_parquet")
    def test_write_single_path(self, mock_write, file_sink, batch_config):
        """Test writing to a single path."""
        inputs = pd.DataFrame([{"data": "test1"}, {"data": "test2"}])
        results, errors = execute_file_sink(file_sink, inputs, batch_config)

        mock_write.assert_called_once_with("/test/output.parquet", index=False)
        assert len(results) == 1
        assert results.iloc[0]["success"]
        assert len(errors) == 0

    @patch("pandas.DataFrame.to_parquet")
    def test_write_multiple_paths(
        self, mock_write, file_sink_no_path, batch_config
    ):
        """Test writing to multiple paths (splits and recurses)."""
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
        assert mock_write.call_count == 2
        assert len(results) == 2
        assert len(errors) == 0

    def test_missing_path_raises_error(self, file_sink_no_path, batch_config):
        """Test error when path cannot be determined."""
        inputs = pd.DataFrame([{"data": "test", "other": "value"}])

        with pytest.raises(InterpreterError, match="No path specified"):
            execute_file_sink(file_sink_no_path, inputs, batch_config)

    @patch(
        "pandas.DataFrame.to_parquet", side_effect=Exception("Write failed")
    )
    def test_write_error_drop_mode(self, mock_write, file_sink, batch_config):
        """Test error handling in DROP mode."""
        batch_config.error_mode = ErrorMode.DROP
        inputs = pd.DataFrame([{"data": "test"}])

        results, errors = execute_file_sink(file_sink, inputs, batch_config)

        assert len(results) == 0
        assert len(errors) == 1
        assert "Write failed" in errors.iloc[0]["error"]
