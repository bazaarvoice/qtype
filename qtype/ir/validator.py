"""
Semantic validation for QType intermediate representation (IR).

This module validates QTypeSpec objects for internal consistency, referential
integrity, and adherence to semantic rules defined in the QType specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from qtype.dsl.model import Agent, QTypeSpec, Tool
from qtype.ir.model import EmbeddingModel, Step


class SemanticValidationError(Exception):
    """Raised when semantic validation fails on a QTypeSpec."""

    def __init__(self, errors: List[str]) -> None:
        super().__init__("Semantic validation failed")
        self.errors = errors

    def __str__(self) -> str:
        return "\n".join(self.errors)


@dataclass(frozen=True)
class ComponentRegistry:
    """Registry of component IDs organized by type for efficient lookups."""

    models: Dict[str, Any]
    inputs: Dict[str, Any]
    prompts: Dict[str, Any]
    outputs: Dict[str, Any]
    memory: Dict[str, Any]
    tool_providers: Dict[str, Any]
    auth_providers: Dict[str, Any]
    feedback: Dict[str, Any]
    retrievers: Dict[str, Any]
    flows: Dict[str, Any]
    steps: Dict[str, Any]
    tools: Dict[str, Any]
    telemetry: Dict[str, Any]


class SemanticValidator:
    """Validates semantic rules for QType specifications."""

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate(self, spec: QTypeSpec) -> None:
        """
        Validate a QTypeSpec for semantic correctness.

        Args:
            spec: The QType specification to validate

        Raises:
            SemanticValidationError: If validation fails with detailed errors
        """
        self._errors.clear()
        registry = self._build_component_registry(spec)

        # Execute all validation rules
        self._validate_unique_ids(spec, registry)
        self._validate_referential_integrity(spec, registry)
        self._validate_flows(spec, registry)
        self._validate_memory_usage(spec, registry)
        self._validate_tooling(spec, registry)
        self._validate_models(spec, registry)
        self._validate_prompts(spec, registry)
        self._validate_circular_dependencies(spec, registry)

        if self._errors:
            raise SemanticValidationError(self._errors)

    def _build_component_registry(self, spec: QTypeSpec) -> ComponentRegistry:
        """Build a registry of all components indexed by ID."""
        registry = ComponentRegistry(
            models={m.id: m for m in spec.models or []},
            inputs={i.id: i for i in spec.variables or []},
            prompts={p.id: p for p in spec.prompts or []},
            outputs={},
            memory={m.id: m for m in spec.memory or []},
            tool_providers={tp.id: tp for tp in spec.tool_providers or []},
            auth_providers={a.id: a for a in spec.auth or []},
            feedback={f.id: f for f in spec.feedback or []},
            retrievers={r.id: r for r in spec.retrievers or []},
            flows={f.id: f for f in spec.flows or []},
            steps={},
            tools={},
            telemetry={t.id: t for t in spec.telemetry or []},
        )

        self._collect_nested_components(spec, registry)
        return registry

    def _collect_nested_components(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Collect tools, outputs, and steps from nested structures."""
        # Collect tools from tool providers - allow same ID across providers
        tool_ids_by_provider: Dict[str, Set[str]] = {}
        for tool_provider in spec.tool_providers or []:
            provider_tool_ids = set()
            for tool in tool_provider.tools or []:
                if tool.id in provider_tool_ids:
                    self._errors.append(
                        f"Duplicate Tool.id: {tool.id} in provider {tool_provider.id}"
                    )
                provider_tool_ids.add(tool.id)
                # Store tools with provider prefix to avoid global collisions
                registry.tools[f"{tool_provider.id}:{tool.id}"] = tool
            tool_ids_by_provider[tool_provider.id] = provider_tool_ids

        # Collect output variables from prompts
        for prompt in spec.prompts or []:
            for output_var in prompt.outputs or []:
                if output_var in registry.outputs:
                    self._errors.append(f"Duplicate Variable.id: {output_var}")
                registry.outputs[output_var] = None

        # Collect steps from flows and their output variables
        # TODO: Update step validation for new DSL structure
        # The DSL has changed significantly - Agent and Tool no longer have component field
        # and Tool doesn't inherit from Actionable, so it doesn't have inputs/outputs
        # For now, just collect step IDs to prevent duplicates
        for flow in spec.flows or []:
            for step in flow.steps:
                if isinstance(step, (Agent, Tool)):
                    if step.id in registry.steps:
                        self._errors.append(f"Duplicate Step.id: {step.id}")
                    registry.steps[step.id] = step

    def _validate_unique_ids(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Ensure all IDs are unique within their component categories."""
        # Check each component type for duplicates
        self._check_component_duplicates(
            "Model", [m.id for m in spec.models or []]
        )
        self._check_component_duplicates(
            "Variable", [i.id for i in spec.variables or []]
        )
        self._check_component_duplicates(
            "Prompt", [p.id for p in spec.prompts or []]
        )
        self._check_component_duplicates(
            "Memory", [m.id for m in spec.memory or []]
        )
        self._check_component_duplicates(
            "ToolProvider", [tp.id for tp in spec.tool_providers or []]
        )
        self._check_component_duplicates(
            "AuthorizationProvider", [a.id for a in spec.auth or []]
        )
        self._check_component_duplicates(
            "Feedback", [f.id for f in spec.feedback or []]
        )
        self._check_component_duplicates(
            "Retriever", [r.id for r in spec.retrievers or []]
        )
        self._check_component_duplicates(
            "Flow", [f.id for f in spec.flows or []]
        )
        self._check_component_duplicates(
            "TelemetrySink", [t.id for t in spec.telemetry or []]
        )
        # Tools and steps are checked separately in _collect_nested_components

    def _check_component_duplicates(
        self, component_type: str, component_ids: List[str]
    ) -> None:
        """Check for duplicate IDs in a component type."""
        seen_ids = set()
        for component_id in component_ids:
            if component_id in seen_ids:
                self._errors.append(
                    f"Duplicate {component_type}.id: {component_id}"
                )
            seen_ids.add(component_id)

    def _validate_referential_integrity(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that all component references point to existing components."""
        self._validate_prompt_references(spec, registry)
        self._validate_step_references(spec, registry)
        self._validate_retriever_references(spec, registry)
        self._validate_memory_references(spec, registry)
        self._validate_tool_provider_references(spec, registry)
        self._validate_telemetry_references(spec, registry)
        self._validate_flow_references(spec, registry)
        self._validate_flow_references(spec, registry)

    def _validate_prompt_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that prompt input/output variables reference existing components."""
        for prompt in spec.prompts or []:
            for input_var in prompt.inputs:
                if input_var not in registry.inputs:
                    self._errors.append(
                        f"Prompt '{prompt.id}' references non-existent "
                        f"input variable '{input_var}'"
                    )

            for output_var in prompt.outputs or []:
                if output_var not in registry.outputs:
                    self._errors.append(
                        f"Prompt '{prompt.id}' references non-existent "
                        f"output variable '{output_var}'"
                    )

    def _validate_step_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that step components and variables reference existing components."""
        for flow in spec.flows or []:
            for step in flow.steps:
                if not isinstance(step, Step):
                    continue

                # Validate step component exists
                component_found = False
                if step.component in registry.prompts:
                    component_found = True
                elif step.component in registry.flows:
                    component_found = True
                elif step.component in registry.retrievers:
                    component_found = True
                else:
                    # Check if it's a tool (stored with provider prefix)
                    for tool_key in registry.tools:
                        if (
                            ":" in tool_key
                            and tool_key.split(":", 1)[1] == step.component
                        ):
                            component_found = True
                            break

                if not component_found:
                    self._errors.append(
                        f"Step '{step.id}' references non-existent "
                        f"component '{step.component}'"
                    )

                # Validate step variables
                for input_var in step.inputs or []:
                    if input_var not in registry.inputs:
                        self._errors.append(
                            f"Step '{step.id}' references non-existent "
                            f"input variable '{input_var}'"
                        )

                for output_var in step.outputs or []:
                    if output_var not in registry.outputs:
                        self._errors.append(
                            f"Step '{step.id}' references non-existent "
                            f"output variable '{output_var}'"
                        )

    def _validate_retriever_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that retrievers reference valid embedding models."""
        for retriever in registry.retrievers.values():
            if not hasattr(retriever, "embedding_model"):
                continue

            embedding_model_id = retriever.embedding_model
            if hasattr(embedding_model_id, "id"):
                embedding_model_id = embedding_model_id.id

            if embedding_model_id not in registry.models:
                self._errors.append(
                    f"Retriever '{retriever.id}' references non-existent "
                    f"embedding model '{embedding_model_id}'"
                )
                continue

            # Validate embedding model type
            embedding_model = registry.models[embedding_model_id]
            if not isinstance(embedding_model, EmbeddingModel):
                self._errors.append(
                    f"Retriever '{retriever.id}' embedding_model must be "
                    f"an instance of EmbeddingModel"
                )

    def _validate_memory_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that memory components reference valid embedding models."""
        for memory in spec.memory or []:
            if memory.embedding_model not in registry.models:
                self._errors.append(
                    f"Memory '{memory.id}' references non-existent "
                    f"embedding model '{memory.embedding_model}'"
                )

    def _validate_tool_provider_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that tool providers reference valid auth providers."""
        for tool_provider in spec.tool_providers or []:
            if (
                tool_provider.auth
                and tool_provider.auth not in registry.auth_providers
            ):
                self._errors.append(
                    f"ToolProvider '{tool_provider.id}' references non-existent "
                    f"auth provider '{tool_provider.auth}'"
                )

    def _validate_telemetry_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that telemetry sinks reference valid auth providers."""
        for telemetry_sink in spec.telemetry or []:
            if (
                telemetry_sink.auth
                and telemetry_sink.auth not in registry.auth_providers
            ):
                self._errors.append(
                    f"TelemetrySink '{telemetry_sink.id}' references non-existent "
                    f"auth provider '{telemetry_sink.auth}'"
                )

    def _validate_flow_references(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate that flows reference valid inputs, outputs, and memory."""
        for flow in spec.flows or []:
            # Validate flow inputs
            for input_id in flow.inputs or []:
                if input_id not in registry.inputs:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"input variable '{input_id}'"
                    )

            # Validate flow outputs
            for output_id in flow.outputs or []:
                if output_id not in registry.outputs:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"output '{output_id}'"
                    )

            # Validate flow memory references
            for memory_id in flow.memory or []:
                if memory_id not in registry.memory:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"memory '{memory_id}'"
                    )

    def _validate_flows(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate flow structure and rules."""
        for flow in spec.flows or []:
            self._validate_flow_steps(flow, registry)
            self._validate_flow_conditions(flow, registry)
            self._validate_flow_memory_rules(flow)

    def _validate_flow_steps(
        self, flow: Any, registry: ComponentRegistry
    ) -> None:
        """Validate flow step uniqueness and references."""
        step_ids: Set[str] = set()

        for step in flow.steps:
            if isinstance(step, Step):
                if step.id in step_ids:
                    self._errors.append(
                        f"Duplicate Step.id '{step.id}' in Flow '{flow.id}'"
                    )
                step_ids.add(step.id)
            elif isinstance(step, str):
                if step not in registry.flows:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"nested flow '{step}'"
                    )

    def _validate_flow_conditions(
        self, flow: Any, registry: ComponentRegistry
    ) -> None:
        """Validate flow conditional logic references."""
        for condition in flow.conditions or []:
            step_ids = {
                step.id for step in flow.steps if isinstance(step, Step)
            }

            for then_id in condition.then:
                if then_id not in step_ids and then_id not in registry.flows:
                    self._errors.append(
                        f"Condition in Flow '{flow.id}' references non-existent "
                        f"step '{then_id}'"
                    )

            for else_id in condition.else_ or []:
                if else_id not in step_ids and else_id not in registry.flows:
                    self._errors.append(
                        f"Condition in Flow '{flow.id}' references non-existent "
                        f"step '{else_id}'"
                    )

    def _validate_flow_memory_rules(self, flow: Any) -> None:
        """Validate flow memory rules based on mode."""
        if flow.mode == "chat":
            if not flow.memory:
                self._errors.append(
                    f"Flow '{flow.id}' with mode 'chat' must define memory"
                )
        else:
            if flow.memory:
                self._errors.append(
                    f"Flow '{flow.id}' with mode '{flow.mode}' "
                    f"must not define memory"
                )

    def _validate_memory_usage(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Ensure Memory IDs are not misused as Step components."""
        memory_ids = {memory.id for memory in spec.memory or []}

        for flow in spec.flows or []:
            for step in flow.steps:
                if isinstance(step, Step) and step.component in memory_ids:
                    self._errors.append(
                        f"Memory '{step.component}' cannot be used as a "
                        f"Step component in Flow '{flow.id}'. "
                        f"Use retrievers for step-level operations."
                    )

    def _validate_tooling(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate tool provider and tool constraints."""
        for tool_provider in spec.tool_providers or []:
            self._validate_tool_uniqueness(tool_provider)
            self._validate_tool_schemas(tool_provider)

    def _validate_tool_uniqueness(self, tool_provider: Any) -> None:
        """Validate tool ID and name uniqueness within a provider."""
        tool_names: Set[str] = set()
        tool_ids: Set[str] = set()

        for tool in tool_provider.tools or []:
            if tool.id in tool_ids:
                self._errors.append(
                    f"Duplicate Tool.id '{tool.id}' in "
                    f"ToolProvider '{tool_provider.id}'"
                )
            tool_ids.add(tool.id)

            if tool.name in tool_names:
                self._errors.append(
                    f"Duplicate Tool.name '{tool.name}' in "
                    f"ToolProvider '{tool_provider.id}'"
                )
            tool_names.add(tool.name)

    def _validate_tool_schemas(self, tool_provider: Any) -> None:
        """Validate that tools have required schemas."""
        for tool in tool_provider.tools or []:
            if not tool.input_schema or not tool.output_schema:
                self._errors.append(
                    f"Tool '{tool.id}' in ToolProvider '{tool_provider.id}' "
                    f"must define both input_schema and output_schema"
                )

    def _validate_models(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate model constraints and embedding model rules."""
        # EmbeddingModel inherits from Model, so it can have inference_params
        # No specific validation needed for now
        pass

    def _validate_prompts(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Validate prompt template/path requirements."""
        for prompt in spec.prompts or []:
            has_template = prompt.template is not None
            has_path = prompt.path is not None

            if has_template == has_path:  # Both true or both false
                self._errors.append(
                    f"Prompt '{prompt.id}' must define either template "
                    f"or path, but not both"
                )

    def _validate_circular_dependencies(
        self, spec: QTypeSpec, registry: ComponentRegistry
    ) -> None:
        """Detect circular references in flow dependencies."""
        for flow in spec.flows or []:
            self._detect_circular_flow_reference(flow.id, set(), registry)

    def _detect_circular_flow_reference(
        self, flow_id: str, visited: Set[str], registry: ComponentRegistry
    ) -> None:
        """Recursively detect circular flow references."""
        if flow_id in visited:
            self._errors.append(
                f"Circular reference detected in Flow '{flow_id}'"
            )
            return

        flow = registry.flows.get(flow_id)
        if not flow:
            return

        visited.add(flow_id)

        for step in flow.steps:
            if isinstance(step, str):  # Nested flow reference
                self._detect_circular_flow_reference(
                    step, visited.copy(), registry
                )


def validate_semantics(spec: QTypeSpec) -> None:
    """
    Validate a QTypeSpec for semantic correctness.

    This function provides a convenient interface to the SemanticValidator class.

    Args:
        spec: The QType specification to validate

    Raises:
        SemanticValidationError: If validation fails with detailed errors
    """
    validator = SemanticValidator()
    validator.validate(spec)
