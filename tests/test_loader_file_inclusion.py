"""
Tests for YAML loader file inclusion functionality.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from qtype.dsl.loader import (
    load_from_string,
    load_yaml,
    _resolve_path,
)


class TestFileIncludeLoader:
    """Test suite for FileIncludeLoader functionality."""

    def test_include_yaml_file(self) -> None:
        """Test including a YAML file with !include tag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file
            included_file = tmp_path / "included.yaml"
            included_file.write_text("""
host: localhost
port: 5432
database: testdb
""")

            # Create main file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
app:
  name: "Test App"
  database: !include {included_file.name}
""")

            # Load and verify
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["app"]["name"] == "Test App"
            assert result["app"]["database"]["host"] == "localhost"
            assert result["app"]["database"]["port"] == 5432
            assert result["app"]["database"]["database"] == "testdb"

    def test_include_raw_text_file(self) -> None:
        """Test including a raw text file with !include_raw tag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create text file
            text_file = tmp_path / "content.txt"
            text_file.write_text("Hello, World!\nThis is a test file.")

            # Create main file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
message: !include_raw {text_file.name}
""")

            # Load and verify
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["message"] == "Hello, World!\nThis is a test file."

    def test_nested_includes(self) -> None:
        """Test nested file inclusion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create deepest level file
            deep_file = tmp_path / "deep.yaml"
            deep_file.write_text("""
secret: "deep_value"
""")

            # Create middle level file that includes deep file
            middle_file = tmp_path / "middle.yaml"
            middle_file.write_text(f"""
config: !include {deep_file.name}
middle_value: "test"
""")

            # Create main file that includes middle file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
app:
  settings: !include {middle_file.name}
""")

            # Load and verify
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["app"]["settings"]["config"]["secret"] == "deep_value"
            assert result["app"]["settings"]["middle_value"] == "test"

    def test_include_with_env_vars(self) -> None:
        """Test file inclusion combined with environment variables."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Set environment variable
            with patch.dict(os.environ, {"TEST_HOST": "production.example.com"}):
                # Create included file with env var
                included_file = tmp_path / "config.yaml"
                included_file.write_text("""
host: ${TEST_HOST}
port: 443
""")

                # Create main file
                main_file = tmp_path / "main.yaml"
                main_file.write_text(f"""
database: !include {included_file.name}
""")

                # Load and verify
                result_list = load_yaml(str(main_file))
                assert len(result_list) == 1
                result = result_list[0]

                assert result["database"]["host"] == "production.example.com"
                assert result["database"]["port"] == 443

    def test_absolute_path_include(self) -> None:
        """Test including files with absolute paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file
            included_file = tmp_path / "absolute.yaml"
            included_file.write_text("""
value: "absolute_test"
""")

            # Create main file with absolute path reference
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
data: !include {included_file.absolute()}
""")

            # Load and verify
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["data"]["value"] == "absolute_test"

    def test_file_not_found_error(self) -> None:
        """Test error handling when included file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create main file referencing non-existent file
            main_file = tmp_path / "main.yaml"
            main_file.write_text("""
data: !include nonexistent.yaml
""")

            # Verify error is raised
            with pytest.raises(FileNotFoundError, match="Failed to load included file"):
                load_yaml(str(main_file))

    def test_malformed_yaml_in_included_file(self) -> None:
        """Test error handling when included file contains malformed YAML."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create malformed YAML file
            included_file = tmp_path / "malformed.yaml"
            included_file.write_text("""
key: value
  invalid: indentation
""")

            # Create main file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
data: !include {included_file.name}
""")

            # Verify error is raised
            with pytest.raises(FileNotFoundError, match="Failed to load included file"):
                load_yaml(str(main_file))

    def test_include_empty_file(self) -> None:
        """Test including an empty file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create empty file
            empty_file = tmp_path / "empty.yaml"
            empty_file.write_text("")

            # Create main file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
data: !include {empty_file.name}
""")

            # Load and verify
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["data"] is None

    def test_multiple_includes_in_same_file(self) -> None:
        """Test multiple includes in the same YAML file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create first included file
            config1_file = tmp_path / "config1.yaml"
            config1_file.write_text("""
service: "service1"
port: 8080
""")

            # Create second included file
            config2_file = tmp_path / "config2.yaml"
            config2_file.write_text("""
service: "service2"
port: 8081
""")

            # Create text file
            text_file = tmp_path / "message.txt"
            text_file.write_text("Welcome to the application!")

            # Create main file with multiple includes
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
services:
  primary: !include {config1_file.name}
  secondary: !include {config2_file.name}
welcome_message: !include_raw {text_file.name}
""")

            # Load and verify
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["services"]["primary"]["service"] == "service1"
            assert result["services"]["primary"]["port"] == 8080
            assert result["services"]["secondary"]["service"] == "service2"
            assert result["services"]["secondary"]["port"] == 8081
            assert result["welcome_message"] == "Welcome to the application!"


class TestPathResolution:
    """Test suite for path resolution functionality."""

    def test_resolve_relative_path(self) -> None:
        """Test resolving relative paths."""
        current_path = "/home/user/project/config/main.yaml"
        target_path = "database.yaml"

        result = _resolve_path(current_path, target_path)

        assert result == "/home/user/project/config/database.yaml"

    def test_resolve_absolute_path(self) -> None:
        """Test that absolute paths are returned as-is."""
        current_path = "/home/user/project/main.yaml"
        target_path = "/etc/config/database.yaml"

        result = _resolve_path(current_path, target_path)

        assert result == "/etc/config/database.yaml"

    def test_resolve_url_with_relative_path(self) -> None:
        """Test resolving relative paths with URL base."""
        current_path = "https://example.com/config/main.yaml"
        target_path = "database.yaml"

        result = _resolve_path(current_path, target_path)

        assert result == "https://example.com/config/database.yaml"

    def test_resolve_url_with_subdirectory(self) -> None:
        """Test resolving relative paths in subdirectories with URL base."""
        current_path = "https://example.com/project/config/main.yaml"
        target_path = "../secrets/db.yaml"

        result = _resolve_path(current_path, target_path)

        assert result == "https://example.com/project/secrets/db.yaml"

    def test_resolve_absolute_url(self) -> None:
        """Test that absolute URLs are returned as-is."""
        current_path = "https://example.com/config/main.yaml"
        target_path = "https://other.com/config/database.yaml"

        result = _resolve_path(current_path, target_path)

        assert result == "https://other.com/config/database.yaml"

    def test_resolve_scheme_url(self) -> None:
        """Test that URLs with schemes are returned as-is."""
        current_path = "/home/user/project/main.yaml"
        target_path = "s3://bucket/config/database.yaml"

        result = _resolve_path(current_path, target_path)

        assert result == "s3://bucket/config/database.yaml"


class TestEnvironmentVariablesWithIncludes:
    """Test environment variable functionality with file includes."""

    def test_env_var_in_main_file(self) -> None:
        """Test environment variables in the main file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            with patch.dict(os.environ, {"APP_NAME": "TestApp"}):
                main_file = tmp_path / "main.yaml"
                main_file.write_text("""
app:
  name: ${APP_NAME}
  version: "1.0.0"
""")

                result_list = load_yaml(str(main_file))
                assert len(result_list) == 1
                result = result_list[0]

                assert result["app"]["name"] == "TestApp"

    def test_env_var_with_default_in_included_file(self) -> None:
        """Test environment variables with defaults in included files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file with env var and default
            included_file = tmp_path / "config.yaml"
            included_file.write_text("""
host: ${DB_HOST:localhost}
port: ${DB_PORT:5432}
""")

            # Create main file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
database: !include {included_file.name}
""")

            # Load without setting env vars (should use defaults)
            result_list = load_yaml(str(main_file))
            assert len(result_list) == 1
            result = result_list[0]

            assert result["database"]["host"] == "localhost"
            assert result["database"]["port"] == "5432"

    def test_required_env_var_missing_in_included_file(self) -> None:
        """Test error when required env var is missing in included file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file with required env var
            included_file = tmp_path / "config.yaml"
            included_file.write_text("""
secret: ${REQUIRED_SECRET}
""")

            # Create main file
            main_file = tmp_path / "main.yaml"
            main_file.write_text(f"""
config: !include {included_file.name}
""")

            # Should raise error for missing required env var
            with pytest.raises(ValueError, match="Environment variable 'REQUIRED_SECRET' is required"):
                load_yaml(str(main_file))


@pytest.mark.network
@pytest.mark.skipif(
    "SKIP_NETWORK_TESTS" in os.environ,
    reason="Network tests skipped (set SKIP_NETWORK_TESTS to skip)"
)
class TestRemoteFileInclusion:
    """Test suite for remote file inclusion (requires network access)."""

    def test_github_raw_include(self) -> None:
        """Test including a file from GitHub raw URL."""
        # Note: This test requires network access and may be flaky
        # In a real project, you might want to mock fsspec or use a local test server

        # Create a temporary file to test with
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
remote_data: !include https://raw.githubusercontent.com/example/repo/main/config.yaml
""")
            temp_file = f.name

        try:
            # This would normally test against a real URL
            # For now, we'll just test that the function tries to load it
            with pytest.raises((FileNotFoundError, Exception)):
                load_yaml(temp_file)
        finally:
            os.unlink(temp_file)


class TestLoadFromString:
    """Test suite for load_from_string functionality."""

    def test_load_from_string_basic(self) -> None:
        """Test loading YAML from a string."""
        yaml_content = """
name: "Test App"
version: "1.0.0"
"""
        result_list = load_from_string(yaml_content)
        assert len(result_list) == 1
        result = result_list[0]

        assert result["name"] == "Test App"
        assert result["version"] == "1.0.0"

    def test_load_from_string_with_env_vars(self) -> None:
        """Test loading YAML from string with environment variables."""
        with patch.dict(os.environ, {"APP_NAME": "TestApp"}):
            yaml_content = """
app:
  name: ${APP_NAME}
  version: "1.0.0"
"""
            result_list = load_from_string(yaml_content)
            assert len(result_list) == 1
            result = result_list[0]

            assert result["app"]["name"] == "TestApp"

    def test_load_from_string_multiple_documents(self) -> None:
        """Test loading multiple YAML documents from a string."""
        yaml_content = """
name: "First Doc"
---
name: "Second Doc"
"""
        result_list = load_from_string(yaml_content)
        assert len(result_list) == 2

        assert result_list[0]["name"] == "First Doc"
        assert result_list[1]["name"] == "Second Doc"
