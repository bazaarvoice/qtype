"""
Unit tests for QType semantic validation - TelemetrySink Rules.

This module tests telemetry sink validation rules including auth provider
references and unique IDs as defined in semantic_ir.md.
"""

import unittest

from qtype.dsl.model import (
    AuthorizationProvider,
    QTypeSpec,
    TelemetrySink,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class TelemetryRulesTest(unittest.TestCase):
    """Test TelemetrySink validation rules."""

    def test_telemetry_sink_without_auth_success(self) -> None:
        """Test that telemetry sink without auth provider passes validation."""
        spec = QTypeSpec(
            version="1.0",
            telemetry=[
                TelemetrySink(
                    id="simple_sink",
                    endpoint="https://telemetry.example.com/events",
                )
            ],
        )
        validate_semantics(spec)

    def test_telemetry_sink_with_valid_auth_success(self) -> None:
        """Test that telemetry sink with valid auth provider passes validation."""
        spec = QTypeSpec(
            version="1.0",
            auth=[
                AuthorizationProvider(
                    id="telemetry_auth",
                    type="api_key",
                    api_key="secret-key",
                )
            ],
            telemetry=[
                TelemetrySink(
                    id="authenticated_sink",
                    endpoint="https://secure-telemetry.example.com/events",
                    auth="telemetry_auth",
                )
            ],
        )
        validate_semantics(spec)

    def test_telemetry_sink_with_invalid_auth_failure(self) -> None:
        """Test that telemetry sink with non-existent auth provider fails validation."""
        spec = QTypeSpec(
            version="1.0",
            telemetry=[
                TelemetrySink(
                    id="broken_sink",
                    endpoint="https://telemetry.example.com/events",
                    auth="nonexistent_auth",
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "TelemetrySink 'broken_sink' references non-existent auth provider 'nonexistent_auth'",
            str(context.exception),
        )

    def test_multiple_telemetry_sinks_with_mixed_auth_success(self) -> None:
        """Test multiple telemetry sinks with different auth configurations."""
        spec = QTypeSpec(
            version="1.0",
            auth=[
                AuthorizationProvider(
                    id="api_key_auth",
                    type="api_key",
                    api_key="secret-key",
                ),
                AuthorizationProvider(
                    id="oauth_auth",
                    type="oauth2",
                    client_id="client-123",
                    client_secret="client-secret",
                    token_url="https://auth.example.com/token",
                ),
            ],
            telemetry=[
                TelemetrySink(
                    id="public_sink",
                    endpoint="https://public-telemetry.example.com/events",
                ),
                TelemetrySink(
                    id="api_key_sink",
                    endpoint="https://api-telemetry.example.com/events",
                    auth="api_key_auth",
                ),
                TelemetrySink(
                    id="oauth_sink",
                    endpoint="https://oauth-telemetry.example.com/events",
                    auth="oauth_auth",
                ),
            ],
        )
        validate_semantics(spec)

    def test_telemetry_sink_auth_reference_to_different_auth_types_success(
        self,
    ) -> None:
        """Test that telemetry sinks can reference different auth provider types."""
        spec = QTypeSpec(
            version="1.0",
            auth=[
                AuthorizationProvider(
                    id="basic_auth",
                    type="api_key",
                    api_key="basic-secret",
                ),
                AuthorizationProvider(
                    id="oauth2_auth",
                    type="oauth2",
                    client_id="oauth-client",
                    client_secret="oauth-secret",
                    token_url="https://oauth.provider.com/token",
                    scopes=["telemetry:write"],
                ),
            ],
            telemetry=[
                TelemetrySink(
                    id="basic_sink",
                    endpoint="https://basic.telemetry.com/events",
                    auth="basic_auth",
                ),
                TelemetrySink(
                    id="oauth_sink",
                    endpoint="https://oauth.telemetry.com/events",
                    auth="oauth2_auth",
                ),
            ],
        )
        validate_semantics(spec)

    def test_empty_telemetry_list_success(self) -> None:
        """Test that empty telemetry list passes validation."""
        spec = QTypeSpec(
            version="1.0",
            telemetry=[],
        )
        validate_semantics(spec)

    def test_none_telemetry_success(self) -> None:
        """Test that None telemetry field passes validation."""
        spec = QTypeSpec(
            version="1.0",
            telemetry=None,
        )
        validate_semantics(spec)

    def test_telemetry_sink_with_complex_endpoint_success(self) -> None:
        """Test that telemetry sink with complex endpoint URLs pass validation."""
        spec = QTypeSpec(
            version="1.0",
            telemetry=[
                TelemetrySink(
                    id="complex_sink",
                    endpoint="https://telemetry.example.com:8443/v2/events?format=json&compression=gzip",
                ),
            ],
        )
        validate_semantics(spec)

    def test_telemetry_sink_reusing_auth_provider_success(self) -> None:
        """Test that multiple telemetry sinks can use the same auth provider."""
        spec = QTypeSpec(
            version="1.0",
            auth=[
                AuthorizationProvider(
                    id="shared_auth",
                    type="api_key",
                    api_key="shared-secret",
                )
            ],
            telemetry=[
                TelemetrySink(
                    id="sink1",
                    endpoint="https://telemetry1.example.com/events",
                    auth="shared_auth",
                ),
                TelemetrySink(
                    id="sink2",
                    endpoint="https://telemetry2.example.com/events",
                    auth="shared_auth",
                ),
            ],
        )
        validate_semantics(spec)


if __name__ == "__main__":
    unittest.main()
