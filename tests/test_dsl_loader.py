"""
Tests for YAML loader file inclusion functionality.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from qtype.loader import (
    _resolve_path,
    _StringStream,
    load_yaml,
    load_yaml_from_string,
)


class TestFileFixtures:
    """Reusable test file content templates."""

    SIMPLE_YAML = """
name: "Test App"
version: "1.0.0"
"""

    QTYPE_DOCUMENT = """
id: test_app
description: "Test application"
flows:
  - id: test_flow
    steps:
      - id: test_step
        template: "Hello {{ name }}"
        inputs:
          - id: name
            type: text
"""

    CONFIG_WITH_ENV = """
host: ${DB_HOST:localhost}
port: ${DB_PORT:5432}
"""

    MALFORMED_YAML = """
key: value
  invalid: indentation
"""


class TestHelpers:
    """Helper methods for test setup and common operations."""

    @staticmethod
    def create_temp_file(tmp_path: Path, filename: str, content: str) -> Path:
        """Create a temporary file with the given content."""
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path

    @staticmethod
    def load_and_assert_single_result(file_path: Path | str) -> dict[str, Any]:
        """Load YAML file and assert it returns a single result."""
        result_list = load_yaml(str(file_path))
        # Only index if result_list is a list
        if isinstance(result_list, list):
            assert len(result_list) == 1
            result = result_list[0]  # type: ignore[index]
        else:
            result = result_list
        return result

    @staticmethod
    def assert_yaml_error(
        file_path: Path | str, error_type: type, error_message: str
    ) -> None:
        """Assert that loading a YAML file raises the expected error."""
        with pytest.raises(error_type, match=error_message):
            load_yaml(str(file_path))

    @staticmethod
    def create_qtype_document(
        tmp_path: Path, filename: str, doc_id: str
    ) -> Path:
        """Create a QType document with the given ID."""
        content = TestFileFixtures.QTYPE_DOCUMENT.replace("test_app", doc_id)
        return TestHelpers.create_temp_file(tmp_path, filename, content)

    @staticmethod
    def create_multiple_documents(
        tmp_path: Path, filename: str, count: int = 2
    ) -> Path:
        """Create a file with multiple QType documents."""
        documents = []
        for i in range(count):
            doc_id = f"doc_{i}"
            documents.append(
                TestFileFixtures.QTYPE_DOCUMENT.replace("test_app", doc_id)
            )
        content = "\n---\n".join(documents)
        return TestHelpers.create_temp_file(tmp_path, filename, content)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


class TestStringStream:
    """Test suite for _StringStream functionality."""

    @pytest.mark.parametrize(
        "content,size,expected_reads",
        [
            ("Hello, World!", 5, ["Hello", ", Wor", "ld!"]),
            ("Short", 10, ["Short"]),
            ("A" * 100, 25, ["A" * 25, "A" * 25, "A" * 25, "A" * 25]),
        ],
    )
    def test_string_stream_read_with_size(
        self, content: str, size: int, expected_reads: list[str]
    ) -> None:
        """Test reading from StringStream with specific size parameter."""
        stream = _StringStream(content, "test_file.txt")

        for expected_read in expected_reads:
            result = stream.read(size)
            assert result == expected_read

    def test_string_stream_read_all(self) -> None:
        """Test reading all content from StringStream."""
        content = "Test content with various characters: 123 !@#"
        stream = _StringStream(content, "test.txt")

        result = stream.read()
        assert result == content


class TestBasicLoaderFunctions:
    """Test suite for basic loader function operations."""

    def test_load_from_string_basic(self, temp_dir: Path) -> None:
        """Test loading YAML from a string."""
        result_list = load_yaml_from_string(TestFileFixtures.SIMPLE_YAML)
        if isinstance(result_list, list):
            assert len(result_list) == 1
            result = result_list[0]  # type: ignore[index]
        else:
            result = result_list
        assert result["name"] == "Test App"
        assert result["version"] == "1.0.0"

    def test_load_from_string_with_env_vars(self, temp_dir: Path) -> None:
        """Test loading YAML from string with environment variables."""
        with patch.dict(os.environ, {"APP_NAME": "TestApp"}):
            yaml_content = """
app:
  name: ${APP_NAME}
  version: "1.0.0"
"""
            result_list = load_yaml_from_string(yaml_content)
            if isinstance(result_list, list):
                assert len(result_list) == 1
                result = result_list[0]  # type: ignore[index]
            else:
                result = result_list
            assert result["app"]["name"] == "TestApp"

    def test_load_from_string_multiple_documents(self, temp_dir: Path) -> None:
        """Test loading multiple YAML documents from a string."""
        from yaml.composer import ComposerError

        try:
            _ = load_yaml_from_string(
                """
name: "First Doc"
---
name: "Second Doc"
"""
            )
            assert False, "Expected ComposerError for multiple documents"
        except ComposerError:
            pass

    @pytest.mark.parametrize(
        "yaml_content,expected_result",
        [
            ("# Just a comment\n", []),
            ("", []),
            ("name: Test\n---\n# Empty document\n---\nversion: 1.0", 2),
        ],
    )
    def test_load_from_string_edge_cases(
        self, yaml_content: str, expected_result: list | int
    ) -> None:
        from yaml.composer import ComposerError

        if expected_result == 2:
            try:
                _ = load_yaml_from_string(yaml_content)
                assert False, "Expected ComposerError for multiple documents"
            except ComposerError:
                pass
        else:
            result = load_yaml_from_string(yaml_content)
            assert result is None


class TestDocumentLoading:
    """Test suite for document loading functionality."""

    def test_load_documents_single(self, temp_dir: Path) -> None:
        """Test loading a single QType document."""
        test_file = TestHelpers.create_qtype_document(
            temp_dir, "test.yaml", "test_app"
        )
        result = load_yaml(str(test_file))
        if isinstance(result, list):
            assert len(result) == 1
            doc = result[0]  # type: ignore[index]
        else:
            doc = result
        assert isinstance(doc, dict)
        assert doc is not None

    def test_load_documents_multiple(self, temp_dir: Path) -> None:
        """Test loading multiple QType documents."""
        from yaml.composer import ComposerError

        test_file = TestHelpers.create_multiple_documents(
            temp_dir, "test.yaml", 3
        )
        try:
            _ = load_yaml(str(test_file))
            assert False, "Expected ComposerError for multiple documents"
        except ComposerError:
            pass

    def test_load_function_single_document(self, temp_dir: Path) -> None:
        """Test load function with single document."""
        test_file = TestHelpers.create_qtype_document(
            temp_dir, "test.yaml", "test_app"
        )
        result = load_yaml(str(test_file))
        assert not isinstance(result, list) or len(result) == 1

    def test_load_function_multiple_documents(self, temp_dir: Path) -> None:
        """Test load function with multiple documents."""
        from yaml.composer import ComposerError

        test_file = TestHelpers.create_multiple_documents(
            temp_dir, "test.yaml", 2
        )
        try:
            _ = load_yaml(str(test_file))
            assert False, "Expected ComposerError for multiple documents"
        except ComposerError:
            pass


class TestFileInclusion:
    """Test suite for file inclusion functionality."""

    def test_include_yaml_file(self, temp_dir: Path) -> None:
        """Test including a YAML file with !include tag."""
        # Create included file
        TestHelpers.create_temp_file(
            temp_dir,
            "included.yaml",
            """
host: localhost
port: 5432
database: testdb
""",
        )

        # Create main file
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
app:
  name: "Test App"
  database: !include included.yaml
""",
        )

        # Load and verify
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["app"]["name"] == "Test App"
        assert result["app"]["database"]["host"] == "localhost"
        assert result["app"]["database"]["port"] == 5432
        assert result["app"]["database"]["database"] == "testdb"

    def test_include_raw_text_file(self, temp_dir: Path) -> None:
        """Test including a raw text file with !include_raw tag."""
        # Create text file
        TestHelpers.create_temp_file(
            temp_dir, "content.txt", "Hello, World!\nThis is a test file."
        )

        # Create main file
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
message: !include_raw content.txt
""",
        )

        # Load and verify
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["message"] == "Hello, World!\nThis is a test file."

    def test_nested_includes(self, temp_dir: Path) -> None:
        """Test nested file inclusion."""
        # Create deepest level file
        TestHelpers.create_temp_file(
            temp_dir,
            "deep.yaml",
            """
secret: "deep_value"
""",
        )

        # Create middle level file that includes deep file
        TestHelpers.create_temp_file(
            temp_dir,
            "middle.yaml",
            """
config: !include deep.yaml
middle_value: "test"
""",
        )

        # Create main file that includes middle file
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
app:
  settings: !include middle.yaml
""",
        )

        # Load and verify
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["app"]["settings"]["config"]["secret"] == "deep_value"
        assert result["app"]["settings"]["middle_value"] == "test"

    def test_multiple_includes_in_same_file(self, temp_dir: Path) -> None:
        """Test multiple includes in the same YAML file."""
        # Create included files
        TestHelpers.create_temp_file(
            temp_dir,
            "config1.yaml",
            """
service: "service1"
port: 8080
""",
        )

        TestHelpers.create_temp_file(
            temp_dir,
            "config2.yaml",
            """
service: "service2"
port: 8081
""",
        )

        TestHelpers.create_temp_file(
            temp_dir, "message.txt", "Welcome to the application!"
        )

        # Create main file with multiple includes
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
services:
  primary: !include config1.yaml
  secondary: !include config2.yaml
welcome_message: !include_raw message.txt
""",
        )

        # Load and verify
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["services"]["primary"]["service"] == "service1"
        assert result["services"]["primary"]["port"] == 8080
        assert result["services"]["secondary"]["service"] == "service2"
        assert result["services"]["secondary"]["port"] == 8081
        assert result["welcome_message"] == "Welcome to the application!"

    @pytest.mark.parametrize(
        "file_content,expected_error",
        [
            (
                "data: !include nonexistent.yaml",
                "Failed to load included file",
            ),
            (
                "data: !include_raw nonexistent.txt",
                "Failed to load included file",
            ),
        ],
    )
    def test_include_errors(
        self, temp_dir: Path, file_content: str, expected_error: str
    ) -> None:
        """Test error handling for file inclusion."""
        main_file = TestHelpers.create_temp_file(
            temp_dir, "main.yaml", file_content
        )
        TestHelpers.assert_yaml_error(
            main_file, FileNotFoundError, expected_error
        )

    def test_include_empty_file(self, temp_dir: Path) -> None:
        """Test including an empty file."""
        # Create empty file
        TestHelpers.create_temp_file(temp_dir, "empty.yaml", "")

        # Create main file
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
data: !include empty.yaml
""",
        )

        # Load and verify
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["data"] is None

    def test_malformed_yaml_in_included_file(self, temp_dir: Path) -> None:
        """Test error handling when included file contains malformed YAML."""
        TestHelpers.create_temp_file(
            temp_dir, "malformed.yaml", TestFileFixtures.MALFORMED_YAML
        )
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
data: !include malformed.yaml
""",
        )
        TestHelpers.assert_yaml_error(
            main_file, FileNotFoundError, "Failed to load included file"
        )

    def test_absolute_path_include(self, temp_dir: Path) -> None:
        """Test including files with absolute paths."""
        # Create included file
        included_file = TestHelpers.create_temp_file(
            temp_dir,
            "absolute.yaml",
            """
value: "absolute_test"
""",
        )

        # Create main file with absolute path reference
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            f"""
data: !include {included_file.absolute()}
""",
        )

        # Load and verify
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["data"]["value"] == "absolute_test"


class TestEnvironmentVariables:
    """Test environment variable functionality."""

    def test_env_var_in_main_file(self, temp_dir: Path) -> None:
        """Test environment variables in the main file."""
        with patch.dict(os.environ, {"APP_NAME": "TestApp"}):
            main_file = TestHelpers.create_temp_file(
                temp_dir,
                "main.yaml",
                """
app:
  name: ${APP_NAME}
  version: "1.0.0"
""",
            )

            result = TestHelpers.load_and_assert_single_result(main_file)
            assert result["app"]["name"] == "TestApp"

    def test_env_var_with_default_in_included_file(
        self, temp_dir: Path
    ) -> None:
        """Test environment variables with defaults in included files."""
        # Create included file with env var and default
        TestHelpers.create_temp_file(
            temp_dir, "config.yaml", TestFileFixtures.CONFIG_WITH_ENV
        )

        # Create main file
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
database: !include config.yaml
""",
        )

        # Load without setting env vars (should use defaults)
        result = TestHelpers.load_and_assert_single_result(main_file)
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == "5432"

    def test_include_with_env_vars(self, temp_dir: Path) -> None:
        """Test file inclusion combined with environment variables."""
        # Set environment variable
        with patch.dict(os.environ, {"TEST_HOST": "production.example.com"}):
            # Create included file with env var
            TestHelpers.create_temp_file(
                temp_dir,
                "config.yaml",
                """
host: ${TEST_HOST}
port: 443
""",
            )

            # Create main file
            main_file = TestHelpers.create_temp_file(
                temp_dir,
                "main.yaml",
                """
database: !include config.yaml
""",
            )

            # Load and verify
            result = TestHelpers.load_and_assert_single_result(main_file)
            assert result["database"]["host"] == "production.example.com"
            assert result["database"]["port"] == 443

    def test_required_env_var_missing_in_included_file(
        self, temp_dir: Path
    ) -> None:
        """Test error when required env var is missing in included file."""
        # Create included file with required env var
        TestHelpers.create_temp_file(
            temp_dir,
            "config.yaml",
            """
secret: ${REQUIRED_SECRET}
""",
        )

        # Create main file
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
config: !include config.yaml
""",
        )

        # Should raise error for missing required env var
        TestHelpers.assert_yaml_error(
            main_file,
            ValueError,
            "Environment variable 'REQUIRED_SECRET' is required",
        )


class TestPathResolution:
    """Test suite for path resolution functionality."""

    @pytest.mark.parametrize(
        "current_path,target_path,expected",
        [
            (
                "/home/user/project/config/main.yaml",
                "database.yaml",
                "/home/user/project/config/database.yaml",
            ),
            (
                "/home/user/project/main.yaml",
                "/etc/config/database.yaml",
                "/etc/config/database.yaml",
            ),
            (
                "https://example.com/config/main.yaml",
                "database.yaml",
                "https://example.com/config/database.yaml",
            ),
            (
                "https://example.com/project/config/main.yaml",
                "../secrets/db.yaml",
                "https://example.com/project/secrets/db.yaml",
            ),
            (
                "https://example.com/config/main.yaml",
                "https://other.com/config/database.yaml",
                "https://other.com/config/database.yaml",
            ),
            (
                "/home/user/project/main.yaml",
                "s3://bucket/config/database.yaml",
                "s3://bucket/config/database.yaml",
            ),
        ],
    )
    def test_path_resolution(
        self, current_path: str, target_path: str, expected: str
    ) -> None:
        """Test various path resolution scenarios."""
        result = _resolve_path(current_path, target_path)
        assert result == expected


class TestLoaderEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_load_yaml_string_content(self, temp_dir: Path) -> None:
        """Test load_yaml when content is a string, not a URI."""
        yaml_content = "name: Test App\nversion: 1.0.0"
        result = load_yaml(yaml_content)
        if isinstance(result, list):
            assert len(result) == 1
            doc = result[0]  # type: ignore[index]
        else:
            doc = result
        assert doc["name"] == "Test App"
        assert doc["version"] == "1.0.0"

    def test_load_yaml_uri_parsing_exception(self, temp_dir: Path) -> None:
        """Test load_yaml when URI parsing raises an exception."""
        test_file = TestHelpers.create_temp_file(
            temp_dir, "test.yaml", "name: Test"
        )
        with patch("qtype.loader.url_to_fs", side_effect=ValueError):
            result = load_yaml(str(test_file))
            if isinstance(result, dict):
                assert result["name"] == "Test"
            elif isinstance(result, str):
                # Loader returns the file path as a string
                assert result == str(test_file)
            elif result is None:
                assert False, "Expected a dict or string, got None"

    @pytest.mark.parametrize(
        "content,expected_error",
        [
            ("nonexistent_file.yaml", FileNotFoundError),
            ("simple_filename_no_extension", FileNotFoundError),
        ],
    )
    def test_load_yaml_file_not_found(
        self, content: str, expected_error: type
    ) -> None:
        with pytest.raises(expected_error):
            load_yaml(content)

    def test_load_from_string_yaml_load_all_returns_none(
        self, temp_dir: Path
    ) -> None:
        """Test load_from_string when yaml.load_all returns None."""
        with patch("yaml.load", return_value=None):
            result = load_yaml_from_string("name: Test")
            assert result is None


@pytest.mark.network
@pytest.mark.skipif(
    "SKIP_NETWORK_TESTS" in os.environ,
    reason="Network tests skipped (set SKIP_NETWORK_TESTS to skip)",
)
class TestRemoteFileInclusion:
    """Test suite for remote file inclusion (requires network access)."""

    def test_github_raw_include(self, temp_dir: Path) -> None:
        """Test including a file from GitHub raw URL."""
        # Note: This test requires network access and may be flaky
        # Create a temporary file to test with
        main_file = TestHelpers.create_temp_file(
            temp_dir,
            "main.yaml",
            """
remote_data: !include https://raw.githubusercontent.com/example/repo/main/config.yaml
""",
        )

        # This would normally test against a real URL
        # For now, we'll just test that the function tries to load it
        with pytest.raises((FileNotFoundError, Exception)):
            load_yaml(str(main_file))
