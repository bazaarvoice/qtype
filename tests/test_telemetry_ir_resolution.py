"""
Unit tests for QType IR resolution - TelemetrySink resolution.

This module tests the IR resolver's ability to correctly resolve TelemetrySink
objects with auth provider references.
"""

import unittest

import qtype.dsl.model as dsl
from qtype.ir.resolver import IRResolutionError, resolve_semantic_ir


class TelemetryResolutionTest(unittest.TestCase):
    """Test TelemetrySink IR resolution."""

    def test_telemetry_sink_without_auth_resolution_success(self) -> None:
        """Test that telemetry sink without auth resolves correctly."""
        dsl_spec = dsl.QTypeSpec(
            version="1.0",
            telemetry=[
                dsl.TelemetrySink(
                    id="simple_sink",
                    endpoint="https://telemetry.example.com/events",
                )
            ],
        )
        ir_spec = resolve_semantic_ir(dsl_spec)

        self.assertEqual(len(ir_spec.telemetry), 1)
        sink = ir_spec.telemetry[0]
        self.assertEqual(sink.id, "simple_sink")
        self.assertEqual(sink.endpoint, "https://telemetry.example.com/events")
        self.assertIsNone(sink.auth)

    def test_telemetry_sink_with_auth_resolution_success(self) -> None:
        """Test that telemetry sink with auth resolves correctly."""
        dsl_spec = dsl.QTypeSpec(
            version="1.0",
            auth=[
                dsl.AuthorizationProvider(
                    id="api_auth",
                    type="api_key",
                    api_key="secret-key",
                )
            ],
            telemetry=[
                dsl.TelemetrySink(
                    id="authenticated_sink",
                    endpoint="https://secure-telemetry.example.com/events",
                    auth="api_auth",
                )
            ],
        )
        ir_spec = resolve_semantic_ir(dsl_spec)

        self.assertEqual(len(ir_spec.telemetry), 1)
        sink = ir_spec.telemetry[0]
        self.assertEqual(sink.id, "authenticated_sink")
        self.assertEqual(sink.endpoint, "https://secure-telemetry.example.com/events")
        self.assertIsNotNone(sink.auth)
        self.assertEqual(sink.auth.id, "api_auth")
        self.assertEqual(sink.auth.type, "api_key")

    def test_telemetry_sink_with_invalid_auth_resolution_failure(self) -> None:
        """Test that telemetry sink with invalid auth reference fails resolution."""
        dsl_spec = dsl.QTypeSpec(
            version="1.0",
            telemetry=[
                dsl.TelemetrySink(
                    id="broken_sink",
                    endpoint="https://telemetry.example.com/events",
                    auth="nonexistent_auth",
                )
            ],
        )

        with self.assertRaises(IRResolutionError) as context:
            resolve_semantic_ir(dsl_spec)
        self.assertIn(
            "Auth provider 'nonexistent_auth' not found",
            str(context.exception),
        )

    def test_multiple_telemetry_sinks_resolution_success(self) -> None:
        """Test that multiple telemetry sinks resolve correctly."""
        dsl_spec = dsl.QTypeSpec(
            version="1.0",
            auth=[
                dsl.AuthorizationProvider(
                    id="auth1",
                    type="api_key",
                    api_key="key1",
                ),
                dsl.AuthorizationProvider(
                    id="auth2",
                    type="oauth2",
                    client_id="client123",
                    client_secret="secret123",
                    token_url="https://oauth.example.com/token",
                ),
            ],
            telemetry=[
                dsl.TelemetrySink(
                    id="sink1",
                    endpoint="https://telemetry1.example.com/events",
                ),
                dsl.TelemetrySink(
                    id="sink2",
                    endpoint="https://telemetry2.example.com/events",
                    auth="auth1",
                ),
                dsl.TelemetrySink(
                    id="sink3",
                    endpoint="https://telemetry3.example.com/events",
                    auth="auth2",
                ),
            ],
        )
        ir_spec = resolve_semantic_ir(dsl_spec)

        self.assertEqual(len(ir_spec.telemetry), 3)

        # Check sink1 (no auth)
        sink1 = ir_spec.telemetry[0]
        self.assertEqual(sink1.id, "sink1")
        self.assertIsNone(sink1.auth)

        # Check sink2 (api_key auth)
        sink2 = ir_spec.telemetry[1]
        self.assertEqual(sink2.id, "sink2")
        self.assertIsNotNone(sink2.auth)
        self.assertEqual(sink2.auth.id, "auth1")
        self.assertEqual(sink2.auth.type, "api_key")

        # Check sink3 (oauth2 auth)
        sink3 = ir_spec.telemetry[2]
        self.assertEqual(sink3.id, "sink3")
        self.assertIsNotNone(sink3.auth)
        self.assertEqual(sink3.auth.id, "auth2")
        self.assertEqual(sink3.auth.type, "oauth2")

    def test_empty_telemetry_resolution_success(self) -> None:
        """Test that empty telemetry list resolves correctly."""
        dsl_spec = dsl.QTypeSpec(
            version="1.0",
            telemetry=[],
        )
        ir_spec = resolve_semantic_ir(dsl_spec)

        self.assertIsNone(ir_spec.telemetry)

    def test_none_telemetry_resolution_success(self) -> None:
        """Test that None telemetry field resolves correctly."""
        dsl_spec = dsl.QTypeSpec(
            version="1.0",
            telemetry=None,
        )
        ir_spec = resolve_semantic_ir(dsl_spec)

        self.assertIsNone(ir_spec.telemetry)


if __name__ == "__main__":
    unittest.main()
