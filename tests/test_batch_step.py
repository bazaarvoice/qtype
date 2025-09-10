"""Unit tests for batch step execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from qtype.interpreter.batch.step import batch_execute_step
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import Condition, Decoder, Flow, SQLSource, Step


@pytest.fixture
def batch_config():
    """Create a default batch config."""
    return BatchConfig(error_mode=ErrorMode.FAIL)


@pytest.fixture
def input_df():
    """Create sample input DataFrame."""
    return pd.DataFrame([{"input": "test"}])


@pytest.fixture
def mock_results():
    """Mock execution results."""
    results = pd.DataFrame([{"output": "processed"}])
    errors = pd.DataFrame()
    return results, errors


class TestBatchExecuteStep:
    """Test the batch_execute_step function."""

    @patch("qtype.interpreter.batch.step.validate_inputs")
    @patch("qtype.interpreter.batch.flow.batch_execute_flow")
    def test_flow_step(
        self,
        mock_batch_execute_flow,
        mock_validate,
        input_df,
        batch_config,
        mock_results,
    ):
        """Test execution of Flow step."""
        flow = MagicMock(spec=Flow)
        mock_batch_execute_flow.return_value = mock_results

        results, errors = batch_execute_step(flow, input_df, batch_config)

        mock_validate.assert_called_once_with(input_df, flow)
        mock_batch_execute_flow.assert_called_once_with(
            flow, input_df, batch_config
        )
        assert results.equals(mock_results[0])
        assert errors.equals(mock_results[1])

    @patch("qtype.interpreter.batch.step.validate_inputs")
    @patch("qtype.interpreter.batch.step.execute_sql_source")
    def test_sql_source_step(
        self,
        mock_execute_sql,
        mock_validate,
        input_df,
        batch_config,
        mock_results,
    ):
        """Test execution of SQLSource step."""
        sql_source = MagicMock(spec=SQLSource)
        mock_execute_sql.return_value = mock_results

        results, errors = batch_execute_step(
            sql_source, input_df, batch_config
        )

        mock_validate.assert_called_once_with(input_df, sql_source)
        mock_execute_sql.assert_called_once_with(
            sql_source, input_df, batch_config
        )
        assert results.equals(mock_results[0])
        assert errors.equals(mock_results[1])

    @patch("qtype.interpreter.batch.step.validate_inputs")
    @patch("qtype.interpreter.batch.step.batch_iterator")
    @patch("qtype.interpreter.batch.step.SINGLE_WRAP_STEPS")
    @pytest.mark.parametrize("step_class", [Decoder, Condition])
    def test_single_wrap_steps(
        self,
        mock_single_wrap_steps,
        mock_batch_iterator,
        mock_validate,
        step_class,
        input_df,
        batch_config,
        mock_results,
    ):
        """Test execution of single wrap steps."""
        step = MagicMock(spec=step_class)
        mock_single_wrap_steps.__contains__ = MagicMock(return_value=True)
        mock_batch_iterator.return_value = mock_results

        results, errors = batch_execute_step(step, input_df, batch_config)

        mock_validate.assert_called_once_with(input_df, step)
        mock_batch_iterator.assert_called_once()
        # Verify partial function was created correctly
        call_args = mock_batch_iterator.call_args
        assert call_args[1]["batch"] is input_df
        assert call_args[1]["batch_config"] is batch_config
        assert results.equals(mock_results[0])
        assert errors.equals(mock_results[1])

    @patch("qtype.interpreter.batch.step.validate_inputs")
    def test_unsupported_step_type(
        self, mock_validate, input_df, batch_config
    ):
        """Test that unsupported step types raise InterpreterError."""
        unsupported_step = MagicMock(spec=Step)

        with pytest.raises(InterpreterError, match="Unsupported step type"):
            batch_execute_step(unsupported_step, input_df, batch_config)

        mock_validate.assert_called_once_with(input_df, unsupported_step)
