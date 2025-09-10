"""Unit tests for batch flow execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from qtype.dsl.base_types import StepCardinality
from qtype.interpreter.batch.flow import batch_execute_flow
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.semantic.model import Flow, Sink, Step


@pytest.fixture
def batch_config():
    """Create a default batch config."""
    return BatchConfig(batch_size=2, error_mode=ErrorMode.FAIL)


@pytest.fixture
def input_df():
    """Create sample input DataFrame."""
    return pd.DataFrame(
        [
            {"user_id": "123", "name": "John"},
            {"user_id": "456", "name": "Jane"},
            {"user_id": "789", "name": "Bob"},
        ]
    )


@pytest.fixture
def mock_step():
    """Create a mock step."""
    step = MagicMock(spec=Step)
    step.id = "test-step"
    step.cardinality = StepCardinality.one
    return step


@pytest.fixture
def mock_sink():
    """Create a mock sink step."""
    sink = MagicMock(spec=Sink)
    sink.id = "test-sink"
    sink.cardinality = StepCardinality.one
    return sink


@pytest.fixture
def sample_flow(mock_step):
    """Create a sample flow with one step."""
    return Flow(
        id="test-flow",
        cardinality=StepCardinality.auto,
        inputs=[],
        outputs=[],
        description=None,
        mode="Complete",
        steps=[mock_step],
    )


@pytest.fixture
def flow_with_sink(mock_sink):
    """Create a flow with a sink step."""
    return Flow(
        id="test-flow-sink",
        cardinality=StepCardinality.auto,
        inputs=[],
        outputs=[],
        description=None,
        mode="Complete",
        steps=[mock_sink],
    )


@pytest.fixture
def multi_step_flow(mock_step, mock_sink):
    """Create a flow with multiple steps."""
    step2 = MagicMock(spec=Step)
    step2.id = "test-step-2"
    step2.cardinality = StepCardinality.one
    return Flow(
        id="test-multi-flow",
        cardinality=StepCardinality.auto,
        inputs=[],
        outputs=[],
        description=None,
        mode="Complete",
        steps=[mock_step, step2, mock_sink],
    )


class TestBatchExecuteFlow:
    """Test the batch_execute_flow function."""

    @patch("qtype.interpreter.batch.flow.batch_execute_step")
    @patch("qtype.interpreter.batch.flow.reconcile_results_and_errors")
    def test_single_step_flow(
        self,
        mock_reconcile,
        mock_execute_step,
        sample_flow,
        input_df,
        batch_config,
    ):
        """Test flow execution with a single step."""
        # Mock step execution results
        step_results = pd.DataFrame([{"result": "processed"}])
        step_errors = pd.DataFrame()
        mock_execute_step.return_value = (step_results, step_errors)

        # Mock reconcile function
        final_results = pd.DataFrame([{"result": "final"}])
        final_errors = pd.DataFrame()
        mock_reconcile.return_value = (final_results, final_errors)

        results, errors = batch_execute_flow(
            sample_flow, input_df, batch_config
        )

        # Verify step was called correctly (batched)
        assert (
            mock_execute_step.call_count == 2
        )  # 3 rows / batch_size 2 = 2 batches
        mock_reconcile.assert_called_once()
        assert results.equals(final_results)
        assert errors.equals(final_errors)

    @patch("qtype.interpreter.batch.flow.batch_execute_step")
    @patch("qtype.interpreter.batch.flow.reconcile_results_and_errors")
    def test_sink_step_not_batched(
        self,
        mock_reconcile,
        mock_execute_step,
        flow_with_sink,
        input_df,
        batch_config,
    ):
        """Test that sink steps receive the entire batch."""
        # Mock step execution results
        step_results = pd.DataFrame([{"result": "sunk"}])
        step_errors = pd.DataFrame()
        mock_execute_step.return_value = (step_results, step_errors)

        # Mock reconcile function
        final_results = pd.DataFrame([{"result": "final"}])
        final_errors = pd.DataFrame()
        mock_reconcile.return_value = (final_results, final_errors)

        batch_execute_flow(flow_with_sink, input_df, batch_config)

        # Verify sink was called once with entire dataset
        mock_execute_step.assert_called_once()
        call_args = mock_execute_step.call_args[0]
        assert len(call_args[1]) == 3  # Entire input dataframe

    @patch("qtype.interpreter.batch.flow.batch_execute_step")
    @patch("qtype.interpreter.batch.flow.reconcile_results_and_errors")
    def test_multi_step_flow(
        self,
        mock_reconcile,
        mock_execute_step,
        multi_step_flow,
        input_df,
        batch_config,
    ):
        """Test flow with multiple steps."""
        # Mock step execution results
        step_results = pd.DataFrame([{"intermediate": "value"}])
        step_errors = pd.DataFrame()
        mock_execute_step.return_value = (step_results, step_errors)

        # Mock reconcile function to return progressive results
        mock_reconcile.side_effect = [
            (step_results, step_errors),  # First step
            (step_results, step_errors),  # Second step
            (step_results, step_errors),  # Sink step
        ]

        batch_execute_flow(multi_step_flow, input_df, batch_config)

        # Should be called for each step
        assert (
            mock_execute_step.call_count == 4
        )  # 2 batches + 1 batch + 1 sink
        assert mock_reconcile.call_count == 3  # One per step

    @patch("qtype.interpreter.batch.flow.batch_execute_step")
    @patch("qtype.interpreter.batch.flow.reconcile_results_and_errors")
    def test_empty_input(
        self,
        mock_reconcile,
        mock_execute_step,
        sample_flow,
        batch_config,
    ):
        """Test flow execution with empty input."""
        empty_df = pd.DataFrame()

        # Mock reconcile function
        final_results = pd.DataFrame()
        final_errors = pd.DataFrame()
        mock_reconcile.return_value = (final_results, final_errors)

        results, errors = batch_execute_flow(
            sample_flow, empty_df, batch_config
        )

        # No step executions should occur
        mock_execute_step.assert_not_called()
        assert len(results) == 0
        assert len(errors) == 0

    @patch("qtype.interpreter.batch.flow.batch_execute_step")
    @patch("qtype.interpreter.batch.flow.reconcile_results_and_errors")
    @patch("qtype.interpreter.batch.flow.logging")
    def test_error_file_writing(
        self,
        mock_logging,
        mock_reconcile,
        mock_execute_step,
        sample_flow,
        input_df,
    ):
        """Test error file writing when write_errors_to is configured."""
        batch_config = BatchConfig(
            write_errors_to="/tmp/errors", error_mode=ErrorMode.DROP
        )

        # Mock step execution results with errors
        step_results = pd.DataFrame([{"result": "ok"}])
        step_errors = pd.DataFrame([{"error": "test error"}])
        mock_execute_step.return_value = (step_results, step_errors)

        # Mock reconcile function
        mock_reconcile.return_value = (step_results, step_errors)

        with patch("pandas.DataFrame.to_parquet") as mock_to_parquet:
            batch_execute_flow(sample_flow, input_df, batch_config)

            # Verify error file was written
            mock_to_parquet.assert_called_once()
            call_args = mock_to_parquet.call_args
            assert "/tmp/errors/test-step.errors.parquet" in call_args[0]

    @patch("qtype.interpreter.batch.flow.batch_execute_step")
    @patch("qtype.interpreter.batch.flow.reconcile_results_and_errors")
    @patch("qtype.interpreter.batch.flow.logging")
    def test_error_file_writing_failure(
        self,
        mock_logging,
        mock_reconcile,
        mock_execute_step,
        sample_flow,
        input_df,
    ):
        """Test handling of error file writing failures."""
        batch_config = BatchConfig(
            write_errors_to="/tmp/errors", error_mode=ErrorMode.DROP
        )

        # Mock step execution results with errors
        step_results = pd.DataFrame([{"result": "ok"}])
        step_errors = pd.DataFrame([{"error": "test error"}])
        mock_execute_step.return_value = (step_results, step_errors)

        # Mock reconcile function
        mock_reconcile.return_value = (step_results, step_errors)

        with patch(
            "pandas.DataFrame.to_parquet",
            side_effect=Exception("Write failed"),
        ):
            batch_execute_flow(sample_flow, input_df, batch_config)

            # Verify warning was logged
            mock_logging.warning.assert_called_once()

    def test_batch_size_calculation(
        self,
        sample_flow,
        input_df,
        batch_config,
    ):
        """Test that batching respects the configured batch size."""
        with patch(
            "qtype.interpreter.batch.flow.batch_execute_step"
        ) as mock_execute_step:
            # Mock step execution results
            step_results = pd.DataFrame([{"result": "processed"}])
            step_errors = pd.DataFrame()
            mock_execute_step.return_value = (step_results, step_errors)

            with patch(
                "qtype.interpreter.batch.flow.reconcile_results_and_errors"
            ) as mock_reconcile:
                mock_reconcile.return_value = (step_results, step_errors)

                batch_execute_flow(sample_flow, input_df, batch_config)

                # With batch_size=2 and 3 input rows, should have 2 calls
                assert mock_execute_step.call_count == 2

                # Check batch sizes
                call_args_list = mock_execute_step.call_args_list
                assert len(call_args_list[0][0][1]) == 2  # First batch: 2 rows
                assert len(call_args_list[1][0][1]) == 1  # Second batch: 1 row
