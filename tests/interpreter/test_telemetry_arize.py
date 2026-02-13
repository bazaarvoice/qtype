"""Unit tests for Arize Cloud telemetry integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from qtype.interpreter.base.secrets import NoOpSecretManager
from qtype.interpreter.feedback_api import (
    ArizeClientWrapper,
    FeedbackRequest,
    ThumbsFeedbackData,
    _create_telemetry_client,
)
from qtype.semantic.model import APIKeyAuthProvider, TelemetrySink


# Shared fixtures
@pytest.fixture
def secret_manager():
    """Reusable NoOp secret manager."""
    return NoOpSecretManager()


@pytest.fixture
def arize_auth():
    """Standard Arize auth configuration."""
    return APIKeyAuthProvider(
        id="arize-auth",
        type="api_key",
        api_key="test-api-key",
    )


@pytest.fixture
def arize_sink(arize_auth):
    """Standard Arize telemetry sink."""
    return TelemetrySink(
        id="arize-sink",
        provider="Arize",
        endpoint="https://otlp.arize.com/v1",
        auth=arize_auth,
        args={
            "space_id": "test-space",
            "project_name": "test-project",
        },
    )


class TestSetupArizeOtel:
    """Tests for _setup_arize_otel() function."""

    @patch("arize.otel.register")
    @patch("qtype.interpreter.telemetry._resolve_arize_credentials")
    def test_calls_arize_register_with_resolved_credentials(
        self,
        mock_resolve_creds,
        mock_arize_register,
        arize_sink,
        secret_manager,
    ):
        """Test arize.otel.register is called with resolved credentials."""
        from qtype.interpreter.telemetry import _setup_arize_otel

        mock_resolve_creds.return_value = (
            "test-space-id",
            "my-project",
            "resolved-key",
        )
        mock_tracer = MagicMock()
        mock_arize_register.return_value = mock_tracer

        result = _setup_arize_otel(
            sink=arize_sink,
            project_id="my-project",
            secret_manager=secret_manager,
        )

        from arize.otel.otel import Transport

        mock_arize_register.assert_called_once_with(
            space_id="test-space-id",
            api_key="resolved-key",
            project_name="my-project",
            endpoint="https://otlp.arize.com/v1",
            transport=Transport.HTTP,
        )
        assert result is mock_tracer

    @pytest.mark.parametrize(
        "missing_field,args,auth",
        [
            (
                "space_id",
                {},
                APIKeyAuthProvider(id="a", type="api_key", api_key="key"),
            ),
            ("auth", {"space_id": "test"}, None),
        ],
    )
    def test_missing_required_field_raises_value_error(
        self, missing_field, args, auth, secret_manager
    ):
        """Test missing required fields raise ValueError."""
        from qtype.interpreter.telemetry import _resolve_arize_credentials

        sink = TelemetrySink(
            id="arize-sink",
            provider="Arize",
            endpoint="https://otlp.arize.com/v1",
            auth=auth,
            args=args,
        )

        with pytest.raises(ValueError, match=missing_field):
            _resolve_arize_credentials(
                sink=sink,
                project_id="proj",
                secret_manager=secret_manager,
            )


class TestRegisterArize:
    """Tests for the Arize branch in register()."""

    @patch("qtype.interpreter.telemetry._setup_arize_otel")
    @patch("qtype.interpreter.telemetry.LlamaIndexInstrumentor")
    def test_register_dispatches_to_arize_setup(
        self, mock_instrumentor_cls, mock_setup, arize_sink, secret_manager
    ):
        """Test register() dispatches to _setup_arize_otel."""
        from qtype.interpreter.telemetry import register

        mock_tracer = MagicMock()
        mock_setup.return_value = mock_tracer

        result = register(arize_sink, secret_manager, project_id="proj")

        mock_setup.assert_called_once_with(
            sink=arize_sink,
            project_id="proj",
            secret_manager=secret_manager,
        )
        assert result is mock_tracer
        mock_instrumentor_cls().instrument.assert_called_once_with(
            tracer_provider=mock_tracer
        )


class TestCreateTelemetryClientArize:
    """Tests for _create_telemetry_client() Arize branch."""

    @patch("arize.ArizeClient")
    @patch("qtype.interpreter.feedback_api._resolve_arize_credentials")
    def test_returns_arize_client_wrapper(
        self,
        mock_resolve_creds,
        mock_arize_client_cls,
        arize_sink,
        secret_manager,
    ):
        """Test Arize branch returns ArizeClientWrapper."""
        mock_resolve_creds.return_value = (
            "test-space",
            "test-project",
            "resolved-key",
        )

        mock_client = MagicMock()
        mock_arize_client_cls.return_value = mock_client

        result = _create_telemetry_client(arize_sink, secret_manager)

        assert isinstance(result, ArizeClientWrapper)
        assert result.client is mock_client
        assert result.space_id == "test-space"
        assert result.project_name == "test-project"
        mock_arize_client_cls.assert_called_once_with(api_key="resolved-key")

    def test_missing_auth_raises_value_error(self, secret_manager):
        """Test missing auth raises ValueError."""
        sink = TelemetrySink(
            id="arize-sink",
            provider="Arize",
            endpoint="https://otlp.arize.com/v1",
            auth=None,
            args={"space_id": "test-space"},
        )
        with pytest.raises(ValueError, match="auth"):
            _create_telemetry_client(sink, secret_manager)


class TestSubmitFeedbackArize:
    """Tests for submit_feedback() Arize branch."""

    @patch("qtype.interpreter.feedback_api._create_telemetry_client")
    def test_submit_thumbs_feedback_calls_update_annotations(
        self, mock_create_client, arize_sink, secret_manager
    ):
        """Test thumbs feedback calls update_annotations correctly."""
        import asyncio

        from qtype.interpreter.feedback_api import create_feedback_endpoint

        mock_arize_client = MagicMock()
        wrapper = ArizeClientWrapper(
            client=mock_arize_client,
            space_id="test-space",
            project_name="test-project",
        )
        mock_create_client.return_value = wrapper

        from fastapi import FastAPI

        app = FastAPI()
        create_feedback_endpoint(app, arize_sink, secret_manager)

        # Find feedback route
        feedback_route = next(
            r
            for r in app.routes
            if hasattr(r, "path") and r.path == "/feedback"
        )

        request = FeedbackRequest(
            span_id="span-123",
            trace_id="trace-456",
            feedback=ThumbsFeedbackData(
                value=True, explanation="Great response"
            ),
        )

        result = asyncio.get_event_loop().run_until_complete(
            feedback_route.endpoint(request)
        )

        assert result.status == "success"
        mock_arize_client.spans.update_annotations.assert_called_once()
        call_kwargs = mock_arize_client.spans.update_annotations.call_args[1]
        assert call_kwargs["space_id"] == "test-space"
        assert call_kwargs["project_name"] == "test-project"
        assert call_kwargs["validate"] is True
