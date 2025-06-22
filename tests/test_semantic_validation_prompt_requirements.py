"""
Unit tests for QType semantic validation - Section 7: Prompt Requirements.

This module tests prompt validation requirements including template/path rules
as defined in semantic_ir.md Section 7.
"""

import unittest

from qtype.dsl.model import Input, Prompt, QTypeSpec, VariableType
from qtype.ir.validator import SemanticValidationError, validate_semantics


class PromptRequirementsTest(unittest.TestCase):
    """Test Section 7: Prompt Requirements validation rules."""

    def test_prompt_with_template_success(self) -> None:
        """Test that prompts with template (and no path) pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="inline_prompt",
                    template="Process this: {user_input}",
                    input_vars=["user_input"],
                    output_vars=["result"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_path_success(self) -> None:
        """Test that prompts with path (and no template) pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="file_prompt",
                    path="prompts/process.txt",
                    input_vars=["user_input"],
                    output_vars=["result"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_both_template_and_path_failure(self) -> None:
        """Test that prompts with both template and path fail validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="invalid_prompt",
                    template="Process this: {user_input}",
                    path="prompts/process.txt",
                    input_vars=["user_input"],
                    output_vars=["result"],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Prompt 'invalid_prompt' must define either template or path, but not both",
            str(context.exception),
        )

    def test_prompt_with_neither_template_nor_path_failure(self) -> None:
        """Test that prompts with neither template nor path fail validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="invalid_prompt",
                    input_vars=["user_input"],
                    output_vars=["result"],
                    # Neither template nor path specified
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Prompt 'invalid_prompt' must define either template or path, but not both",
            str(context.exception),
        )

    def test_prompt_input_vars_reference_existing_inputs_success(self) -> None:
        """Test that prompt input_vars must reference existing Input components."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Input(id="name", type=VariableType.text),
                Input(id="age", type=VariableType.number),
            ],
            prompts=[
                Prompt(
                    id="greeting",
                    template="Hello {name}, you are {age} years old",
                    input_vars=["name", "age"],
                    output_vars=["greeting_message"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_template_variables_extraction_success(self) -> None:
        """Test that template variables are correctly identified and validated."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Input(id="user_name", type=VariableType.text),
                Input(id="context", type=VariableType.text),
                Input(id="task", type=VariableType.text),
            ],
            prompts=[
                Prompt(
                    id="complex_prompt",
                    template="Hello {user_name}! Given this context: {context}, please {task}.",
                    input_vars=["user_name", "context", "task"],
                    output_vars=["response"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_optional_output_vars_success(self) -> None:
        """Test that prompts with no output_vars pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="no_output_prompt",
                    template="Just process: {user_input}",
                    input_vars=["user_input"],
                    # No output_vars specified
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_empty_output_vars_success(self) -> None:
        """Test that prompts with empty output_vars list pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="empty_output_prompt",
                    template="Process: {user_input}",
                    input_vars=["user_input"],
                    output_vars=[],  # Empty list
                )
            ],
        )
        validate_semantics(spec)

    def test_multiple_prompts_with_different_input_vars_success(self) -> None:
        """Test that multiple prompts with different input variable sets pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Input(id="user_name", type=VariableType.text),
                Input(id="user_email", type=VariableType.text),
                Input(id="message", type=VariableType.text),
            ],
            prompts=[
                Prompt(
                    id="greeting_prompt",
                    template="Hello {user_name}!",
                    input_vars=["user_name"],
                    output_vars=["greeting"],
                ),
                Prompt(
                    id="email_prompt",
                    template="Send email to {user_email}: {message}",
                    input_vars=["user_email", "message"],
                    output_vars=["email_sent"],
                ),
                Prompt(
                    id="full_prompt",
                    template="Hi {user_name}, sending {message} to {user_email}",
                    input_vars=["user_name", "user_email", "message"],
                    output_vars=["full_response"],
                ),
            ],
        )
        validate_semantics(spec)

    def test_prompt_path_with_valid_extension_success(self) -> None:
        """Test that prompt paths with various valid extensions pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="txt_prompt",
                    path="prompts/system.txt",
                    input_vars=["input"],
                ),
                Prompt(
                    id="md_prompt",
                    path="prompts/user.md",
                    input_vars=["input"],
                ),
                Prompt(
                    id="jinja_prompt",
                    path="prompts/template.j2",
                    input_vars=["input"],
                ),
            ],
        )
        validate_semantics(spec)


if __name__ == "__main__":
    unittest.main()
