"""
Unit tests for QType semantic validation - Section 5: Tooling Rules.

This module tests tooling validation rules including tool uniqueness and schema
requirements as defined in semantic_ir.md Section 5.
"""

import unittest

from qtype.dsl.model import QTypeSpec, Tool, ToolProvider
from qtype.ir.validator import SemanticValidationError, validate_semantics


class ToolingRulesTest(unittest.TestCase):
    """Test Section 5: Tooling Rules validation rules."""

    def test_tool_ids_unique_within_provider_success(self) -> None:
        """Test that tool IDs are unique within a provider."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="First Tool",
                            description="First tool description",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        ),
                        Tool(
                            id="tool2",
                            name="Second Tool",
                            description="Second tool description",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        ),
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_tool_names_unique_within_provider_success(self) -> None:
        """Test that tool names are unique within a provider."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Unique Tool Name 1",
                            description="First tool description",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        ),
                        Tool(
                            id="tool2",
                            name="Unique Tool Name 2",
                            description="Second tool description",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        ),
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_duplicate_tool_names_within_provider_failure(self) -> None:
        """Test that duplicate tool names within a provider fail validation."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Duplicate Name",
                            description="First tool description",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        ),
                        Tool(
                            id="tool2",
                            name="Duplicate Name",
                            description="Second tool description",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        ),
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Duplicate Tool.name 'Duplicate Name' in ToolProvider 'provider1'",
            str(context.exception),
        )

    def test_tool_defines_both_schemas_success(self) -> None:
        """Test that tools with both input and output schemas pass validation."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Complete Tool",
                            description="Tool with both schemas",
                            input_schema={
                                "type": "object",
                                "properties": {"input": {"type": "string"}},
                            },
                            output_schema={
                                "type": "object",
                                "properties": {"output": {"type": "string"}},
                            },
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_tool_missing_input_schema_failure(self) -> None:
        """Test that tools missing input schema fail validation."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Incomplete Tool",
                            description="Tool without input schema",
                            input_schema={},  # Empty schema counts as missing
                            output_schema={"type": "object"},
                        )
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Tool 'tool1' in ToolProvider 'provider1' must define both input_schema and output_schema",
            str(context.exception),
        )

    def test_tool_missing_output_schema_failure(self) -> None:
        """Test that tools missing output schema fail validation."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Incomplete Tool",
                            description="Tool without output schema",
                            input_schema={"type": "object"},
                            output_schema={},  # Empty schema counts as missing
                        )
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Tool 'tool1' in ToolProvider 'provider1' must define both input_schema and output_schema",
            str(context.exception),
        )

    def test_openapi_spec_with_empty_tools_success(self) -> None:
        """Test that tool providers with OpenAPI spec and empty tools pass validation."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="OpenAPI Provider",
                    tools=[],  # Empty tools list is valid with openapi_spec
                    openapi_spec="https://api.example.com/openapi.json",
                )
            ],
        )
        validate_semantics(spec)

    def test_tool_provider_with_include_exclude_tags_success(self) -> None:
        """Test that tool providers with include/exclude tags pass validation."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="Filtered Provider",
                    tools=[],
                    openapi_spec="https://api.example.com/openapi.json",
                    include_tags=["users", "posts"],
                    exclude_paths=["/admin/*", "/internal/*"],
                )
            ],
        )
        validate_semantics(spec)

    def test_tools_across_different_providers_can_have_same_names_success(
        self,
    ) -> None:
        """Test that tools in different providers can have the same names."""
        spec = QTypeSpec(
            version="1.0",
            tool_providers=[
                ToolProvider(
                    id="provider1",
                    name="First Provider",
                    tools=[
                        Tool(
                            id="search",
                            name="search",
                            description="Search in provider1",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        )
                    ],
                ),
                ToolProvider(
                    id="provider2",
                    name="Second Provider",
                    tools=[
                        Tool(
                            id="search",
                            name="search",
                            description="Search in provider2",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                        )
                    ],
                ),
            ],
        )
        validate_semantics(spec)


if __name__ == "__main__":
    unittest.main()
