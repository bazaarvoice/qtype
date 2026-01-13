"""
Test environment variable substitution as documented in How-To guide.

This test validates the examples from:
docs/How-To Guides/Language Features/use_environment_variables.md
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from qtype.dsl.loader import YAMLLoadError, load_yaml_string


class TestEnvironmentVariableSubstitution:
    """Test env var substitution matches How-To documentation."""

    def test_required_env_var(self) -> None:
        """Test ${VAR_NAME} syntax for required variables."""
        yaml_content = """
auths:
  - type: api_key
    id: openai_auth
    api_key: ${OPENAI_KEY}
    host: https://api.openai.com
"""
        with patch.dict(os.environ, {"OPENAI_KEY": "sk-test-key-123"}):
            result = load_yaml_string(yaml_content)

        assert result["auths"][0]["api_key"] == "sk-test-key-123"

    def test_required_env_var_missing_raises_error(self) -> None:
        """Test ${VAR_NAME} raises error when variable not set."""
        yaml_content = """
auths:
  - type: api_key
    id: openai_auth
    api_key: ${QTYPE_TEST_MISSING_VAR}
    host: https://api.openai.com
"""
        # Ensure var is not set
        env_without_key = {
            k: v
            for k, v in os.environ.items()
            if k != "QTYPE_TEST_MISSING_VAR"
        }

        with patch.dict(os.environ, env_without_key, clear=True):
            with pytest.raises(
                YAMLLoadError,
                match="Environment variable 'QTYPE_TEST_MISSING_VAR' is required",
            ):
                load_yaml_string(yaml_content)

    def test_optional_env_var_with_default(self) -> None:
        """Test ${VAR_NAME:-default} syntax uses default when not set."""
        yaml_content = """
models:
  - type: Model
    id: gpt4
    provider: openai
    model_id: ${MODEL_NAME:-gpt-4}
"""
        # Ensure MODEL_NAME is not set
        env_without_var = {
            k: v for k, v in os.environ.items() if k != "MODEL_NAME"
        }

        with patch.dict(os.environ, env_without_var, clear=True):
            result = load_yaml_string(yaml_content)

        assert result["models"][0]["model_id"] == "gpt-4"

    def test_optional_env_var_with_default_uses_env_when_set(self) -> None:
        """Test ${VAR_NAME:-default} prefers env var over default."""
        yaml_content = """
models:
  - type: Model
    id: gpt4
    provider: openai
    model_id: ${MODEL_NAME:-gpt-4}
"""
        with patch.dict(os.environ, {"MODEL_NAME": "gpt-4-turbo"}):
            result = load_yaml_string(yaml_content)

        assert result["models"][0]["model_id"] == "gpt-4-turbo"

    def test_env_vars_work_everywhere_in_yaml(self) -> None:
        """Test env vars can be used in any string value."""
        yaml_content = """
id: ${APP_ID}
description: ${APP_DESC:-Default description}
config:
  host: ${DB_HOST}
  port: ${DB_PORT:-5432}
  nested:
    value: ${NESTED_VAL}
"""
        with patch.dict(
            os.environ,
            {
                "APP_ID": "test-app",
                "DB_HOST": "localhost",
                "NESTED_VAL": "nested-value",
            },
            clear=True,
        ):
            result = load_yaml_string(yaml_content)

        assert result["id"] == "test-app"
        assert result["description"] == "Default description"
        assert result["config"]["host"] == "localhost"
        assert result["config"]["port"] == "5432"
        assert result["config"]["nested"]["value"] == "nested-value"

    def test_empty_default_value(self) -> None:
        """Test ${VAR_NAME:-} uses empty string as default."""
        yaml_content = """
value: ${EMPTY_VAR:-}
"""
        env_without_var = {
            k: v for k, v in os.environ.items() if k != "EMPTY_VAR"
        }

        with patch.dict(os.environ, env_without_var, clear=True):
            result = load_yaml_string(yaml_content)

        assert result["value"] == ""

    def test_default_with_special_characters(self) -> None:
        """Test defaults can contain colons and other characters."""
        yaml_content = """
url: ${API_URL:-https://api.example.com:8080/v1}
"""
        env_without_var = {
            k: v for k, v in os.environ.items() if k != "API_URL"
        }

        with patch.dict(os.environ, env_without_var, clear=True):
            result = load_yaml_string(yaml_content)

        assert result["url"] == "https://api.example.com:8080/v1"
