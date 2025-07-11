"""
Tests for YAML loader file inclusion functionality.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch, Mock

import pytest

from qtype.dsl.loader import (
    load_from_string,
    load_yaml,
    load_documents,
    load,
    _resolve_path,
    _StringStream,
    _resolve_root,
)
from qtype.dsl.model import Document


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
        assert len(result_list) == 1
        return result_list[0]

    @staticmethod
    def assert_yaml_error(
        file_path: Path | str, error_type: type, error_message: str
    ) -> None:
        """Assert that loading a YAML file raises the expected error."""
        with pytest.raises(error_type, match=error_message):
            load_yaml(str(file_path))


class TestStringStream:
    """Test suite for _StringStream functionality."""

    def test_string_stream_read_with_size(self) -> None:
        """Test reading from StringStream with specific size parameter."""
        content = "Hello, World!\nThis is a test."
        stream = _StringStream(content, "test_file.txt")

        # Test reading specific number of characters
        result = stream.read(5)
        assert result == "Hello"

        # Test reading more characters
        result = stream.read(7)
        assert result == ", World"

        # Test reading remaining content
        result = stream.read(-1)
        assert result == "!\nThis is a test."

    def test_string_stream_read_all(self) -> None:
        """Test reading all content from StringStream."""
        content = "Test content"
        stream = _StringStream(content, "test.txt")

        result = stream.read()
        assert result == content


class TestIncludeRawConstructorExceptions:
    """Test suite for _include_raw_constructor exception handling."""

    def test_include_raw_file_not_found(self) -> None:
        """Test _include_raw_constructor with non-existent file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create main file with include_raw pointing to non-existent file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
content: !include_raw nonexistent.txt
""",
            )

            # Should raise FileNotFoundError
            with pytest.raises(
                FileNotFoundError, match="Failed to load included file"
            ):
                load_yaml(str(main_file))


class TestLoadFromStringEdgeCases:
    """Test suite for load_from_string edge cases."""

    def test_load_from_string_empty_results(self) -> None:
        """Test load_from_string when YAML returns None."""
        # Create YAML that results in None
        yaml_content = "# Just a comment\n"

        # This should handle the case where results is None
        result = load_from_string(yaml_content)
        assert result == []

    def test_load_from_string_with_null_documents(self) -> None:
        """Test load_from_string filtering out None documents."""
        # Create YAML with null document
        yaml_content = """
name: "Test"
---
# Empty document
---
version: "1.0"
"""

        result = load_from_string(yaml_content)
        # Should filter out None documents
        assert len(result) == 2
        assert result[0]["name"] == "Test"
        assert result[1]["version"] == "1.0"

    def test_load_from_string_yaml_load_all_returns_none(self) -> None:
        """Test load_from_string when yaml.load_all returns None."""
        # This is a very edge case - we need to mock yaml.load_all to return None
        with patch("yaml.load_all") as mock_load_all:
            mock_load_all.return_value = None

            result = load_from_string("test: value")
            assert result == []


class TestLoadYamlStringContent:
    """Test suite for load_yaml with string content (not URI)."""

    def test_load_yaml_string_content(self) -> None:
        """Test load_yaml when content is a string, not a URI."""
        # Use content that definitely won't be mistaken for a URI
        yaml_content = "name: Test App\nversion: 1.0.0"

        # This should trigger the is_uri = False path
        result = load_yaml(yaml_content)
        assert len(result) == 1
        assert result[0]["name"] == "Test App"
        assert result[0]["version"] == "1.0.0"


class TestLoadYamlUriParsingException:
    """Test suite for URI parsing exception handling."""

    def test_load_yaml_uri_parsing_exception(self) -> None:
        """Test load_yaml when URI parsing raises an exception."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a file
            test_file = TestHelpers.create_temp_file(
                tmp_path,
                "test.yaml",
                """
name: "Test"
""",
            )

            # Mock urlparse to raise an exception
            with patch("qtype.dsl.loader.urlparse") as mock_urlparse:
                mock_urlparse.side_effect = Exception("Parsing error")

                # Should still work despite the exception
                result = load_yaml(str(test_file))
                assert len(result) == 1
                assert result[0]["name"] == "Test"


class TestLoadDocuments:
    """Test suite for load_documents function."""

    def test_load_documents_basic(self) -> None:
        """Test load_documents with basic YAML content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a simple QType document
            test_file = TestHelpers.create_temp_file(
                tmp_path,
                "test.yaml",
                """
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
""",
            )

            documents = load_documents(str(test_file))
            assert len(documents) == 1
            assert isinstance(documents[0], Document)
            # Check that the document was parsed correctly
            assert documents[0].root is not None

    def test_load_documents_multiple(self) -> None:
        """Test load_documents with multiple documents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create multiple QType documents
            test_file = TestHelpers.create_temp_file(
                tmp_path,
                "test.yaml",
                """
id: test_app1
description: "Test application 1"
flows:
  - id: test_flow1
    steps:
      - id: test_step1
        template: "Hello {{ name }}"
        inputs:
          - id: name
            type: text
---
id: test_app2
description: "Test application 2"
flows:
  - id: test_flow2
    steps:
      - id: test_step2
        template: "Hello {{ name }}"
        inputs:
          - id: name
            type: text
""",
            )

            documents = load_documents(str(test_file))
            assert len(documents) == 2
            assert all(isinstance(doc, Document) for doc in documents)
            assert documents[0].root is not None
            assert documents[1].root is not None


class TestResolveRoot:
    """Test suite for _resolve_root function."""

    def test_resolve_root_with_non_list_type(self) -> None:
        """Test _resolve_root with non-list type."""
        mock_doc = Mock()
        mock_doc.root = "direct_root"

        result = _resolve_root(mock_doc)
        assert result == "direct_root"

    def test_resolve_root_with_none(self) -> None:
        """Test _resolve_root with None root."""
        mock_doc = Mock()
        mock_doc.root = None

        result = _resolve_root(mock_doc)
        assert result is None


class TestLoadFunction:
    """Test suite for load function."""

    def test_load_single_document(self) -> None:
        """Test load function with single document."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a simple QType document
            test_file = TestHelpers.create_temp_file(
                tmp_path,
                "test.yaml",
                """
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
""",
            )

            result = load(str(test_file))
            # Should return single resolved document, not a list
            assert not isinstance(result, list)

    def test_load_multiple_documents(self) -> None:
        """Test load function with multiple documents."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create multiple QType documents
            test_file = TestHelpers.create_temp_file(
                tmp_path,
                "test.yaml",
                """
id: test_app1
description: "Test application 1"
flows:
  - id: test_flow1
    steps:
      - id: test_step1
        template: "Hello {{ name }}"
        inputs:
          - id: name
            type: text
---
id: test_app2
description: "Test application 2"
flows:
  - id: test_flow2
    steps:
      - id: test_step2
        template: "Hello {{ name }}"
        inputs:
          - id: name
            type: text
""",
            )

            result = load(str(test_file))
            # Should return list of resolved documents
            assert isinstance(result, list)
            assert len(result) == 2


class TestFileIncludeLoader:
    """Test suite for FileIncludeLoader functionality."""

    def test_include_yaml_file(self) -> None:
        """Test including a YAML file with !include tag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file
            TestHelpers.create_temp_file(
                tmp_path,
                "included.yaml",
                """
host: localhost
port: 5432
database: testdb
""",
            )

            # Create main file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
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

    def test_include_raw_text_file(self) -> None:
        """Test including a raw text file with !include_raw tag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create text file
            TestHelpers.create_temp_file(
                tmp_path, "content.txt", "Hello, World!\nThis is a test file."
            )

            # Create main file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
message: !include_raw content.txt
""",
            )

            # Load and verify
            result = TestHelpers.load_and_assert_single_result(main_file)
            assert result["message"] == "Hello, World!\nThis is a test file."

    def test_nested_includes(self) -> None:
        """Test nested file inclusion."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create deepest level file
            TestHelpers.create_temp_file(
                tmp_path,
                "deep.yaml",
                """
secret: "deep_value"
""",
            )

            # Create middle level file that includes deep file
            TestHelpers.create_temp_file(
                tmp_path,
                "middle.yaml",
                """
config: !include deep.yaml
middle_value: "test"
""",
            )

            # Create main file that includes middle file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
app:
  settings: !include middle.yaml
""",
            )

            # Load and verify
            result = TestHelpers.load_and_assert_single_result(main_file)
            assert (
                result["app"]["settings"]["config"]["secret"] == "deep_value"
            )
            assert result["app"]["settings"]["middle_value"] == "test"

    def test_include_with_env_vars(self) -> None:
        """Test file inclusion combined with environment variables."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Set environment variable
            with patch.dict(
                os.environ, {"TEST_HOST": "production.example.com"}
            ):
                # Create included file with env var
                TestHelpers.create_temp_file(
                    tmp_path,
                    "config.yaml",
                    """
host: ${TEST_HOST}
port: 443
""",
                )

                # Create main file
                main_file = TestHelpers.create_temp_file(
                    tmp_path,
                    "main.yaml",
                    """
database: !include config.yaml
""",
                )

                # Load and verify
                result = TestHelpers.load_and_assert_single_result(main_file)
                assert result["database"]["host"] == "production.example.com"
                assert result["database"]["port"] == 443

    def test_absolute_path_include(self) -> None:
        """Test including files with absolute paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file
            included_file = TestHelpers.create_temp_file(
                tmp_path,
                "absolute.yaml",
                """
value: "absolute_test"
""",
            )

            # Create main file with absolute path reference
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                f"""
data: !include {included_file.absolute()}
""",
            )

            # Load and verify
            result = TestHelpers.load_and_assert_single_result(main_file)
            assert result["data"]["value"] == "absolute_test"

    def test_file_not_found_error(self) -> None:
        """Test error handling when included file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create main file referencing non-existent file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
data: !include nonexistent.yaml
""",
            )

            # Verify error is raised
            TestHelpers.assert_yaml_error(
                main_file, FileNotFoundError, "Failed to load included file"
            )

    def test_malformed_yaml_in_included_file(self) -> None:
        """Test error handling when included file contains malformed YAML."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create malformed YAML file
            TestHelpers.create_temp_file(
                tmp_path,
                "malformed.yaml",
                """
key: value
  invalid: indentation
""",
            )

            # Create main file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
data: !include malformed.yaml
""",
            )

            # Verify error is raised
            TestHelpers.assert_yaml_error(
                main_file, FileNotFoundError, "Failed to load included file"
            )

    def test_include_empty_file(self) -> None:
        """Test including an empty file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create empty file
            TestHelpers.create_temp_file(tmp_path, "empty.yaml", "")

            # Create main file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
data: !include empty.yaml
""",
            )

            # Load and verify
            result = TestHelpers.load_and_assert_single_result(main_file)
            assert result["data"] is None

    def test_multiple_includes_in_same_file(self) -> None:
        """Test multiple includes in the same YAML file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create first included file
            TestHelpers.create_temp_file(
                tmp_path,
                "config1.yaml",
                """
service: "service1"
port: 8080
""",
            )

            # Create second included file
            TestHelpers.create_temp_file(
                tmp_path,
                "config2.yaml",
                """
service: "service2"
port: 8081
""",
            )

            # Create text file
            TestHelpers.create_temp_file(
                tmp_path, "message.txt", "Welcome to the application!"
            )

            # Create main file with multiple includes
            main_file = TestHelpers.create_temp_file(
                tmp_path,
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


class TestEnvironmentVariablesWithIncludes:
    """Test environment variable functionality with file includes."""

    def test_env_var_in_main_file(self) -> None:
        """Test environment variables in the main file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            with patch.dict(os.environ, {"APP_NAME": "TestApp"}):
                main_file = TestHelpers.create_temp_file(
                    tmp_path,
                    "main.yaml",
                    """
app:
  name: ${APP_NAME}
  version: "1.0.0"
""",
                )

                result = TestHelpers.load_and_assert_single_result(main_file)
                assert result["app"]["name"] == "TestApp"

    def test_env_var_with_default_in_included_file(self) -> None:
        """Test environment variables with defaults in included files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file with env var and default
            TestHelpers.create_temp_file(
                tmp_path,
                "config.yaml",
                """
host: ${DB_HOST:localhost}
port: ${DB_PORT:5432}
""",
            )

            # Create main file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
                "main.yaml",
                """
database: !include config.yaml
""",
            )

            # Load without setting env vars (should use defaults)
            result = TestHelpers.load_and_assert_single_result(main_file)
            assert result["database"]["host"] == "localhost"
            assert result["database"]["port"] == "5432"

    def test_required_env_var_missing_in_included_file(self) -> None:
        """Test error when required env var is missing in included file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create included file with required env var
            TestHelpers.create_temp_file(
                tmp_path,
                "config.yaml",
                """
secret: ${REQUIRED_SECRET}
""",
            )

            # Create main file
            main_file = TestHelpers.create_temp_file(
                tmp_path,
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


@pytest.mark.network
@pytest.mark.skipif(
    "SKIP_NETWORK_TESTS" in os.environ,
    reason="Network tests skipped (set SKIP_NETWORK_TESTS to skip)",
)
class TestRemoteFileInclusion:
    """Test suite for remote file inclusion (requires network access)."""

    def test_github_raw_include(self) -> None:
        """Test including a file from GitHub raw URL."""
        # Note: This test requires network access and may be flaky
        # In a real project, you might want to mock fsspec or use a local test server

        # Create a temporary file to test with
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
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

    def test_load_from_string_yaml_load_all_returns_none(self) -> None:
        """Test load_from_string when yaml.load_all returns None."""
        # This is a very edge case - we need to mock yaml.load_all to return None
        with patch("yaml.load_all") as mock_load_all:
            mock_load_all.return_value = None

            result = load_from_string("test: value")
            assert result == []


class TestLoadYamlUriDetectionEdgeCases:
    """Test suite for URI detection edge cases in load_yaml."""

    def test_load_yaml_simple_string_fallback(self) -> None:
        """Test load_yaml with a simple string that goes through url_to_fs fallback."""
        # Use a simple string that doesn't look like YAML or URI
        content = "simple_filename.yaml"

        # This should go through the url_to_fs fallback path but ultimately fail
        # because the file doesn't exist
        with pytest.raises(FileNotFoundError):
            load_yaml(content)

    def test_load_yaml_urlparse_exception(self) -> None:
        """Test load_yaml when urlparse raises an exception."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a file
            test_file = TestHelpers.create_temp_file(
                tmp_path, "test.yaml", "name: Test"
            )

            # Mock urlparse to raise an exception in the URI parsing section
            with patch("qtype.dsl.loader.urlparse") as mock_urlparse:
                mock_urlparse.side_effect = Exception("Parsing error")

                # Should still work despite the urlparse exception
                result = load_yaml(str(test_file))
                assert len(result) == 1
                assert result[0]["name"] == "Test"

    def test_load_yaml_uri_detection_else_branch(self) -> None:
        """Test the else branch in URI detection when content doesn't look like YAML."""
        # Create content that will not trigger the YAML detection but will go through URI path
        # Use a simple filename that doesn't exist
        content = "nonexistent_file.yaml"

        # This should trigger the else branch in URI detection
        # Lines 291-292: the url_to_fs call in the else block
        with pytest.raises(FileNotFoundError):
            load_yaml(content)

    def test_load_yaml_uri_detection_no_newlines(self) -> None:
        """Test the fallback path when content has no newlines."""
        # Create content without newlines that doesn't look like YAML
        content = "simple_filename_no_extension"

        # This should trigger lines 294-295: url_to_fs in the fallback path
        with pytest.raises(FileNotFoundError):
            load_yaml(content)
