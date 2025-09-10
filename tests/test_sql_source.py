"""Unit tests for SQL source batch processing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy.exc import SQLAlchemyError

from qtype.base.exceptions import InterpreterError
from qtype.interpreter.batch.sql_source import (
    execute_sql_source,
    to_output_columns,
)
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.semantic.model import APIKeyAuthProvider, SQLSource, Variable


@pytest.fixture
def sample_sql_source():
    """Create a sample SQLSource for testing."""
    return SQLSource(
        id="test-sql-source",
        query="SELECT name, age FROM users WHERE id = :user_id",
        connection="sqlite:///test.db",
        cardinality="many",
        auth=None,
        inputs=[Variable(id="user_id", type="string", value=None)],
        outputs=[
            Variable(id="name", type="string", value=None),
            Variable(id="age", type="integer", value=None),
        ],
    )


@pytest.fixture
def batch_config():
    """Create a default batch config."""
    return BatchConfig(error_mode=ErrorMode.FAIL)


@pytest.fixture
def input_df():
    """Create sample input DataFrame."""
    return pd.DataFrame([{"user_id": "123"}, {"user_id": "456"}])


@pytest.fixture
def mock_db_engine():
    """Create a mock database engine with connection."""
    mock_connection = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    return mock_engine, mock_connection


@pytest.fixture
def mock_sql_result():
    """Create a mock SQL result."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [("John", 25), ("Jane", 30)]
    mock_result.keys.return_value = ["name", "age"]
    return mock_result


@pytest.fixture
def auth_provider():
    """Create an API key auth provider for testing."""
    return APIKeyAuthProvider(
        id="test-auth",
        type="api_key",
        api_key="test-key",
        host="test-host",
    )


@pytest.fixture
def mock_patches():
    """Common patches for SQL source tests."""
    with (
        patch(
            "qtype.interpreter.batch.sql_source.create_engine"
        ) as mock_create_engine,
        patch(
            "qtype.interpreter.batch.sql_source.validate_inputs"
        ) as mock_validate,
    ):
        yield mock_create_engine, mock_validate


class TestToOutputColumns:
    """Test the to_output_columns function."""

    def test_filters_columns_correctly(self):
        """Test that only specified columns are returned."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        output_columns = {"a", "c"}
        result = to_output_columns(df, output_columns)
        assert list(result.columns) == ["a", "c"]
        assert result.equals(df[["a", "c"]])

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        output_columns = {"a", "b"}
        result = to_output_columns(df, output_columns)
        assert result.equals(df)

    def test_missing_columns_raises_error(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({"a": [1, 2]})
        output_columns = {"a", "missing_col"}
        with pytest.raises(
            InterpreterError, match="SQL Result was missing expected columns"
        ):
            to_output_columns(df, output_columns)


class TestExecuteSQLSource:
    """Test the execute_sql_source function."""

    def test_successful_execution(
        self,
        sample_sql_source,
        input_df,
        batch_config,
        mock_db_engine,
        mock_sql_result,
        mock_patches,
    ):
        """Test successful SQL execution."""
        mock_create_engine, mock_validate = mock_patches
        mock_engine, mock_connection = mock_db_engine
        mock_create_engine.return_value = mock_engine
        mock_connection.execute.return_value = mock_sql_result

        results, errors = execute_sql_source(
            sample_sql_source, input_df, batch_config
        )

        # Verify results
        assert len(results) == 4  # 2 rows * 2 input rows
        assert len(errors) == 0
        assert all(col in results.columns for col in ["name", "age"])
        mock_validate.assert_called_once_with(input_df, sample_sql_source)

    @pytest.mark.parametrize(
        "error_mode,should_raise",
        [
            (ErrorMode.FAIL, True),
            (ErrorMode.DROP, False),
        ],
    )
    def test_sql_error_handling(
        self,
        sample_sql_source,
        input_df,
        mock_db_engine,
        mock_patches,
        error_mode,
        should_raise,
    ):
        """Test SQL error handling in different modes."""
        mock_create_engine, mock_validate = mock_patches
        mock_engine, _ = mock_db_engine
        mock_engine.connect.side_effect = SQLAlchemyError("Database error")
        mock_create_engine.return_value = mock_engine

        batch_config = BatchConfig(error_mode=error_mode)

        if should_raise:
            with pytest.raises(SQLAlchemyError):
                execute_sql_source(sample_sql_source, input_df, batch_config)
        else:
            results, errors = execute_sql_source(
                sample_sql_source, input_df, batch_config
            )
            # Verify error handling
            assert len(results) == 0
            assert len(errors) == 2  # One error per input row
            assert "error" in errors.columns

    @patch("qtype.interpreter.batch.sql_source.auth")
    def test_with_authentication(
        self,
        mock_auth,
        batch_config,
        auth_provider,
        mock_db_engine,
        mock_patches,
    ):
        """Test SQL execution with authentication."""
        mock_create_engine, mock_validate = mock_patches

        # Create SQL source with auth
        sql_source = SQLSource(
            id="test-sql-source",
            query="SELECT * FROM table",
            connection="postgresql://test",
            cardinality="many",
            auth=auth_provider,
            inputs=[],
            outputs=[Variable(id="result", type="string", value=None)],
        )

        mock_session = MagicMock()
        mock_auth.return_value.__enter__.return_value = mock_session

        mock_engine, mock_connection = mock_db_engine
        mock_create_engine.return_value = mock_engine

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("test",)]
        mock_result.keys.return_value = ["result"]
        mock_connection.execute.return_value = mock_result

        input_df = pd.DataFrame([{}])  # Empty input for this test
        execute_sql_source(sql_source, input_df, batch_config)

        # Verify auth was called
        mock_auth.assert_called_once_with(sql_source.auth)

    def test_parameter_injection(
        self,
        sample_sql_source,
        batch_config,
        mock_db_engine,
        mock_sql_result,
        mock_patches,
    ):
        """Test that input parameters are correctly injected into SQL queries."""
        mock_create_engine, mock_validate = mock_patches
        mock_engine, mock_connection = mock_db_engine
        mock_create_engine.return_value = mock_engine
        mock_connection.execute.return_value = mock_sql_result

        input_df = pd.DataFrame([{"user_id": "123", "extra_col": "ignored"}])
        execute_sql_source(sample_sql_source, input_df, batch_config)

        # Verify the execute call received correct parameters
        call_args = mock_connection.execute.call_args
        assert call_args[1]["parameters"] == {"user_id": "123"}
