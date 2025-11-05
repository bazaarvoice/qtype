"""
Shared test fixtures for interpreter tests.

This module provides common fixtures used across multiple test modules
to reduce duplication and ensure consistency.
"""

from __future__ import annotations

import pytest
from opentelemetry import trace

from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.secrets import NoOpSecretManager


@pytest.fixture
def executor_context():
    """
    Shared executor context for testing.

    Provides a standard ExecutorContext with NoOpSecretManager
    and a basic tracer for use in executor tests.
    """
    return ExecutorContext(
        secret_manager=NoOpSecretManager(),
        tracer=trace.get_tracer(__name__),
    )


@pytest.fixture
def secret_manager():
    """Create a NoOpSecretManager for testing."""
    return NoOpSecretManager()
