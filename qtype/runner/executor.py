"""
Flow execution engine for QType specifications.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from qtype.semantic.model import (
    AuthorizationProvider,
    EmbeddingModel,
    Flow,
    Model,
    Prompt,
    QTypeSpec,
    Step,
    Variable,
)

logger = logging.getLogger(__name__)


class FlowExecutionError(Exception):
    """Raised when there's an error during flow execution."""

    pass


class FlowExecutor:
    """
    Executes QType flows by managing prompts, inputs, and model interactions.
    """

    def __init__(self, spec: QTypeSpec):
        """
        Initialize the flow executor with a resolved QType specification.

        Args:
            spec: The resolved IR specification containing all components.
        """
        self.spec = spec
        self.context: Dict[str, Any] = {}

    def execute_flow(self, flow: Flow) -> Optional[str]:
        """
        Execute a complete flow by collecting inputs and running steps.

        Args:
            flow: The flow to execute.

        Returns:
            The final result of the flow execution, if any.

        Raises:
            FlowExecutionError: If flow execution fails.
        """
        logger.info(f"Starting execution of flow: {flow.id}")

        # Collect all required inputs from the flow steps
        required_inputs = self._collect_required_inputs(flow)

        # Collect inputs for the flow
        if required_inputs:
            self._collect_inputs(required_inputs)

        # Execute all steps in the flow
        result = None
        for step in flow.steps:
            result = self._execute_step(step)

        return result

    def _collect_required_inputs(self, flow: Flow) -> List[Variable]:
        """
        Collect all required inputs from the flow and its steps.

        Args:
            flow: The flow to analyze.

        Returns:
            List of unique input objects required by the flow.
        """
        inputs_seen = set()
        required_inputs = []

        # Check flow-level inputs first
        if flow.inputs:
            for inp in flow.inputs:
                if inp.id not in inputs_seen:
                    required_inputs.append(inp)
                    inputs_seen.add(inp.id)

        # Collect inputs from steps
        for step in flow.steps:
            self._collect_inputs_from_step(step, required_inputs, inputs_seen)

        return required_inputs

    def _collect_inputs_from_step(
        self, step: Step, required_inputs: List[Variable], inputs_seen: set
    ) -> None:
        """
        Recursively collect inputs from a step and its components.

        Args:
            step: The step to analyze.
            required_inputs: List to append found inputs to.
            inputs_seen: Set of input IDs already seen.
        """
        # Check step-level inputs
        if step.inputs:
            for inp in step.inputs:
                if inp.id not in inputs_seen:
                    required_inputs.append(inp)
                    inputs_seen.add(inp.id)

        # Check component inputs (if it's a prompt)
        if step.component and isinstance(step.component, Prompt):
            if step.component.inputs:
                for inp in step.component.inputs:
                    if inp.id not in inputs_seen:
                        required_inputs.append(inp)
                        inputs_seen.add(inp.id)

    def _collect_inputs(self, inputs: List[Variable]) -> None:
        """
        Collect input values from the user via command line prompts.

        Args:
            inputs: List of input specifications to collect.
        """
        print("\n" + "=" * 50)
        print("INPUTS REQUIRED")
        print("=" * 50)

        for inp in inputs:
            display_name = inp.display_name or inp.id
            prompt_text = f"{display_name}"

            if inp.display_type and inp.display_type.value == "textarea":
                prompt_text += " (press Ctrl+D when finished)"

            prompt_text += ": "

            if inp.display_type and inp.display_type.value == "textarea":
                print(prompt_text)
                lines = []
                try:
                    while True:
                        line = input()
                        lines.append(line)
                except EOFError:
                    pass
                value = "\n".join(lines)
            else:
                value = input(prompt_text)

            self.context[inp.id] = value
            logger.debug(f"Collected input '{inp.id}': {value}")

    def _execute_step(self, step: Step) -> Optional[str]:
        """
        Execute a single step in the flow.

        Args:
            step: The step to execute.

        Returns:
            The result of the step execution, if any.

        Raises:
            FlowExecutionError: If step execution fails.
        """
        logger.info(f"Executing step: {step.id}")

        if not step.component:
            logger.warning(f"Step '{step.id}' has no component to execute")
            return None

        # Handle different component types
        if isinstance(step.component, Prompt):
            return self._execute_prompt_step(step.component)
        else:
            raise FlowExecutionError(
                f"Unsupported component type: {type(step.component)}"
            )

    def _execute_prompt_step(self, prompt: Prompt) -> str:
        """
        Execute a prompt step by rendering the template and calling the model.

        Args:
            prompt: The prompt component to execute.

        Returns:
            The result of the prompt execution.

        Raises:
            FlowExecutionError: If prompt execution fails.
        """
        if not prompt.template:
            raise FlowExecutionError(
                f"Prompt '{prompt.id}' has no template to execute"
            )

        # Simple template rendering - replace {{ variable }} with values
        rendered_template = prompt.template
        for var_name, value in self.context.items():
            placeholder = f"{{{{ {var_name} }}}}"
            rendered_template = rendered_template.replace(
                placeholder, str(value)
            )

        logger.info(f"Rendered prompt template for '{prompt.id}'")
        logger.debug(f"Template content: {rendered_template}")

        # Find the appropriate model to use for this prompt
        model = self._get_prompt_model()
        if not model:
            raise FlowExecutionError(
                "No suitable model found for prompt execution"
            )

        # Get the auth provider for the model
        auth_provider = self._get_auth_provider(model.provider)
        if not auth_provider:
            raise FlowExecutionError(
                f"No auth provider found for provider '{model.provider}'"
            )

        # Call the actual model
        try:
            response = self._call_model(
                model, auth_provider, rendered_template
            )
        except Exception as e:
            raise FlowExecutionError(f"Model call failed: {str(e)}")

        print("\n🤖 Generated Response:")
        print("-" * 30)
        print(response)
        print("-" * 30)

        return response

    def _get_prompt_model(self) -> Optional[Model]:
        """
        Get the first available non-embedding model for prompt execution.

        Returns:
            The model to use, or None if no suitable model found.
        """
        if not self.spec.models:
            return None

        # Find the first non-embedding model
        for model in self.spec.models:
            if not isinstance(model, EmbeddingModel):
                return model

        return None

    def _get_auth_provider(
        self, provider_name: str
    ) -> Optional[AuthorizationProvider]:
        """
        Get the auth provider for a given provider name.

        Args:
            provider_name: The name of the provider (e.g., 'openai').

        Returns:
            The auth provider, or None if not found.
        """
        if not self.spec.auth:
            return None

        # Find auth provider by ID matching the provider name
        for auth in self.spec.auth:
            if auth.id == provider_name:
                return auth

        return None

    def _call_model(
        self, model: Model, auth_provider: AuthorizationProvider, prompt: str
    ) -> str:
        """
        Call the model with the given prompt.

        Args:
            model: The model configuration to use.
            auth_provider: The auth provider for the model.
            prompt: The rendered prompt text.

        Returns:
            The model's response.

        Raises:
            FlowExecutionError: If the model call fails.
        """
        if model.provider == "openai":
            return self._call_openai_model(model, auth_provider, prompt)
        else:
            raise FlowExecutionError(
                f"Unsupported model provider: {model.provider}"
            )

    def _call_openai_model(
        self, model: Model, auth_provider: AuthorizationProvider, prompt: str
    ) -> str:
        """
        Call an OpenAI model with the given prompt.

        Args:
            model: The OpenAI model configuration.
            auth_provider: The auth provider with the API key.
            prompt: The rendered prompt text.

        Returns:
            The model's response.

        Raises:
            FlowExecutionError: If the OpenAI call fails.
        """
        if not auth_provider.api_key:
            raise FlowExecutionError("OpenAI auth provider missing api_key")

        try:
            client = OpenAI(api_key=auth_provider.api_key)

            # Determine the model ID to use
            model_id = model.model_id or model.id

            # Prepare the inference parameters
            inference_params = model.inference_params or {}

            # Ensure we have required parameters
            call_params = {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                **inference_params,
            }

            logger.info(
                f"Calling OpenAI model '{model_id}' with params: {call_params}"
            )

            response = client.chat.completions.create(**call_params)

            if not response.choices:
                raise FlowExecutionError("OpenAI returned no choices")

            content = response.choices[0].message.content
            if content is None:
                raise FlowExecutionError(
                    "OpenAI returned empty response content"
                )

            return str(content)

        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise FlowExecutionError(f"OpenAI API call failed: {str(e)}")

    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate a mock response to simulate model behavior.

        Args:
            prompt: The rendered prompt text.

        Returns:
            A mock response string.
        """
        # Show that we're processing the actual prompt content
        prompt_lower = prompt.lower()

        if "machine learning" in prompt_lower:
            return "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed for every task."
        elif "capital" in prompt_lower and "france" in prompt_lower:
            return "The capital of France is Paris."
        elif "hello" in prompt_lower:
            return "Hello. How can I help you today?"
        elif "what is" in prompt_lower:
            return "That's a great question. Based on your inquiry, here's what I can tell you about that topic..."
        elif "how" in prompt_lower:
            return "Here's how you can approach this problem..."
        else:
            return f"Thank you for your question. I've processed your prompt: '{prompt[:100]}...' and here's my response based on that."
