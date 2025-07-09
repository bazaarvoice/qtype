"""
Unit tests for QType semantic validation - Section 7: Prompt Requirements.

This module tests prompt validation requirements including template/path rules
as defined in semantic_ir.md Section 7.
"""

import unittest

from qtype.dsl.model import Variable, Prompt, QTypeSpec, VariableType
from qtype.ir.validator import SemanticValidationError, validate_semantics


class PromptRequirementsTest(unittest.TestCase):
    """Test Section 7: Prompt Requirements validation rules."""

    def test_prompt_with_template_success(self) -> None:
        """Test that prompts with template (and no path) pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="inline_prompt",
                    template="Process this: {user_input}",
                    inputs=["user_input"],
                    outputs=["result"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_path_success(self) -> None:
        """Test that prompts with path (and no template) pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="file_prompt",
                    path="prompts/process.txt",
                    inputs=["user_input"],
                    outputs=["result"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_both_template_and_path_failure(self) -> None:
        """Test that prompts with both template and path fail validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="invalid_prompt",
                    template="Process this: {user_input}",
                    path="prompts/process.txt",
                    inputs=["user_input"],
                    outputs=["result"],
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
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="invalid_prompt",
                    inputs=["user_input"],
                    outputs=["result"],
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

    def test_prompt_inputs_reference_existing_inputs_success(self) -> None:
        """Test that prompt inputs must reference existing Variable components."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Variable(id="name", type=VariableType.text),
                Variable(id="age", type=VariableType.number),
            ],
            prompts=[
                Prompt(
                    id="greeting",
                    template="Hello {name}, you are {age} years old",
                    inputs=["name", "age"],
                    outputs=["greeting_message"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_template_variables_extraction_success(self) -> None:
        """Test that template variables are correctly identified and validated."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Variable(id="user_name", type=VariableType.text),
                Variable(id="context", type=VariableType.text),
                Variable(id="task", type=VariableType.text),
            ],
            prompts=[
                Prompt(
                    id="complex_prompt",
                    template="Hello {user_name}! Given this context: {context}, please {task}.",
                    inputs=["user_name", "context", "task"],
                    outputs=["response"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_optional_outputs_success(self) -> None:
        """Test that prompts with no outputs pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="no_output_prompt",
                    template="Just process: {user_input}",
                    inputs=["user_input"],
                    # No outputs specified
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_with_empty_outputs_success(self) -> None:
        """Test that prompts with empty outputs list pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="empty_output_prompt",
                    template="Process: {user_input}",
                    inputs=["user_input"],
                    outputs=[],  # Empty list
                )
            ],
        )
        validate_semantics(spec)

    def test_multiple_prompts_with_different_inputs_success(self) -> None:
        """Test that multiple prompts with different input variable sets pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Variable(id="user_name", type=VariableType.text),
                Variable(id="user_email", type=VariableType.text),
                Variable(id="message", type=VariableType.text),
            ],
            prompts=[
                Prompt(
                    id="greeting_prompt",
                    template="Hello {user_name}!",
                    inputs=["user_name"],
                    outputs=["greeting"],
                ),
                Prompt(
                    id="email_prompt",
                    template="Send email to {user_email}: {message}",
                    inputs=["user_email", "message"],
                    outputs=["email_sent"],
                ),
                Prompt(
                    id="full_prompt",
                    template="Hi {user_name}, sending {message} to {user_email}",
                    inputs=["user_name", "user_email", "message"],
                    outputs=["full_response"],
                ),
            ],
        )
        validate_semantics(spec)

    def test_prompt_path_with_valid_extension_success(self) -> None:
        """Test that prompt paths with various valid extensions pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="txt_prompt",
                    path="prompts/system.txt",
                    inputs=["input"],
                ),
                Prompt(
                    id="md_prompt",
                    path="prompts/user.md",
                    inputs=["input"],
                ),
                Prompt(
                    id="jinja_prompt",
                    path="prompts/template.j2",
                    inputs=["input"],
                ),
            ],
        )
        validate_semantics(spec)


if __name__ == "__main__":
    unittest.main()
