"""
Semantic validation for QType intermediate representation (IR).

This module validates QTypeSpec objects for internal consistency, referential
integrity, and adherence to semantic rules as defined in the QType specification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from qtype.dsl.models import EmbeddingModel, QTypeSpec, Step


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
        self._validate_unique_ids(registry)
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
            inputs={i.id: i for i in spec.inputs or []},
            prompts={p.id: p for p in spec.prompts or []},
            outputs={},
            memory={m.id: m for m in spec.memory or []},
            tool_providers={tp.id: tp for tp in spec.tools or []},
            auth_providers={a.id: a for a in spec.auth or []},
            feedback={f.id: f for f in spec.feedback or []},
            retrievers={r.id: r for r in spec.retrievers or []},
            flows={f.id: f for f in spec.flows or []},
            steps={},
            tools={},
        )
        
        self._collect_nested_components(spec, registry)
        return registry
    
    def _collect_nested_components(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Collect tools, outputs, and steps from nested structures."""
        # Collect tools from tool providers
        for tool_provider in spec.tools or []:
            for tool in tool_provider.tools or []:
                if tool.id in registry.tools:
                    self._errors.append(f"Duplicate Tool.id: {tool.id}")
                registry.tools[tool.id] = tool
        
        # Collect output variables from prompts
        for prompt in spec.prompts or []:
            for output_var in prompt.output_vars or []:
                registry.outputs[output_var] = None
        
        # Collect steps from flows and their output variables
        for flow in spec.flows or []:
            for step in flow.steps:
                if isinstance(step, Step):
                    if step.id in registry.steps:
                        self._errors.append(f"Duplicate Step.id: {step.id}")
                    registry.steps[step.id] = step
                    
                    for output_var in step.output_vars or []:
                        if output_var in registry.outputs:
                            self._errors.append(f"Duplicate Output.id: {output_var}")
                        registry.outputs[output_var] = None

    
    def _validate_unique_ids(self, registry: ComponentRegistry) -> None:
        """Ensure all IDs are unique within their component categories."""
        component_types = [
            ("Model", registry.models),
            ("Input", registry.inputs),
            ("Prompt", registry.prompts),
            ("Memory", registry.memory),
            ("ToolProvider", registry.tool_providers),
            ("AuthorizationProvider", registry.auth_providers),
            ("Feedback", registry.feedback),
            ("Retriever", registry.retrievers),
            ("Flow", registry.flows),
            ("Step", registry.steps),
            ("Tool", registry.tools),
        ]
        
        for component_type, components in component_types:
            seen_ids: Set[str] = set()
            for component_id in components:
                if component_id in seen_ids:
                    self._errors.append(
                        f"Duplicate {component_type}.id: {component_id}"
                    )
                seen_ids.add(component_id)
    
    def _validate_referential_integrity(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate that all component references point to existing components."""
        self._validate_prompt_references(spec, registry)
        self._validate_step_references(spec, registry)
        self._validate_retriever_references(spec, registry)
        self._validate_memory_references(spec, registry)
        self._validate_tool_provider_references(spec, registry)
        self._validate_flow_references(spec, registry)
    
    def _validate_prompt_references(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate that prompt input/output variables reference existing components."""
        for prompt in spec.prompts or []:
            for input_var in prompt.input_vars:
                if input_var not in registry.inputs:
                    self._errors.append(
                        f"Prompt '{prompt.id}' references non-existent "
                        f"input variable '{input_var}'"
                    )
            
            for output_var in prompt.output_vars or []:
                if output_var not in registry.outputs:
                    self._errors.append(
                        f"Prompt '{prompt.id}' references non-existent "
                        f"output variable '{output_var}'"
                    )
    
    def _validate_step_references(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate that step components and variables reference existing components."""
        for flow in spec.flows or []:
            for step in flow.steps:
                if not isinstance(step, Step):
                    continue
                
                # Validate step component exists
                component_found = any(
                    step.component in components
                    for components in [
                        registry.prompts,
                        registry.tools,
                        registry.flows,
                        registry.retrievers,
                    ]
                )
                
                if not component_found:
                    self._errors.append(
                        f"Step '{step.id}' references non-existent "
                        f"component '{step.component}'"
                    )
                
                # Validate step variables
                for input_var in step.input_vars or []:
                    if input_var not in registry.inputs:
                        self._errors.append(
                            f"Step '{step.id}' references non-existent "
                            f"input variable '{input_var}'"
                        )
                
                for output_var in step.output_vars or []:
                    if output_var not in registry.outputs:
                        self._errors.append(
                            f"Step '{step.id}' references non-existent "
                            f"output variable '{output_var}'"
                        )
    
    def _validate_retriever_references(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
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
            
            # Validate embedding model type
            if (hasattr(retriever, "embedding_model") and 
                not isinstance(retriever.embedding_model, EmbeddingModel)):
                self._errors.append(
                    f"Retriever '{retriever.id}' embedding_model must be "
                    f"an instance of EmbeddingModel"
                )
    
    def _validate_memory_references(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate that memory components reference valid embedding models."""
        for memory in spec.memory or []:
            if memory.embedding_model not in registry.models:
                self._errors.append(
                    f"Memory '{memory.id}' references non-existent "
                    f"embedding model '{memory.embedding_model}'"
                )
    
    def _validate_tool_provider_references(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate that tool providers reference valid auth providers."""
        for tool_provider in spec.tools or []:
            if tool_provider.auth and tool_provider.auth not in registry.auth_providers:
                self._errors.append(
                    f"ToolProvider '{tool_provider.id}' references non-existent "
                    f"auth provider '{tool_provider.auth}'"
                )
    
    def _validate_flow_references(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate that flows reference valid inputs, outputs, and memory."""
        for flow in spec.flows or []:
            for input_var in flow.inputs or []:
                if input_var not in registry.inputs:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"input variable '{input_var}'"
                    )
            
            for output_var in flow.outputs or []:
                if output_var not in registry.outputs:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"output variable '{output_var}'"
                    )
            
            for memory_id in flow.memory or []:
                if memory_id not in registry.memory:
                    self._errors.append(
                        f"Flow '{flow.id}' references non-existent "
                        f"memory '{memory_id}'"
                    )

    
    def _validate_flows(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate flow structure and rules."""
        for flow in spec.flows or []:
            self._validate_flow_steps(flow, registry)
            self._validate_flow_conditions(flow, registry)
            self._validate_flow_memory_rules(flow)
    
    def _validate_flow_steps(
        self, 
        flow: Any, 
        registry: ComponentRegistry
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
        self, 
        flow: Any, 
        registry: ComponentRegistry
    ) -> None:
        """Validate flow conditional logic references."""
        for condition in flow.conditions or []:
            step_ids = {
                step.id for step in flow.steps if isinstance(step, Step)
            }
            
            for then_id in condition.then:
                if (then_id not in step_ids and 
                    then_id not in registry.flows):
                    self._errors.append(
                        f"Flow '{flow.id}' condition references non-existent "
                        f"step or flow '{then_id}' in then clause"
                    )
            
            for else_id in condition.else_ or []:
                if (else_id not in step_ids and 
                    else_id not in registry.flows):
                    self._errors.append(
                        f"Flow '{flow.id}' condition references non-existent "
                        f"step or flow '{else_id}' in else clause"
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
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
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
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate tool provider and tool constraints."""
        for tool_provider in spec.tools or []:
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
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Validate model constraints and embedding model rules."""
        for model in spec.models or []:
            if isinstance(model, EmbeddingModel):
                if hasattr(model, "inference_params"):
                    self._errors.append(
                        f"EmbeddingModel '{model.id}' must not have "
                        f"inference_params (reserved for Model instances)"
                    )
            
            if hasattr(model, "model"):
                self._errors.append(
                    f"Model '{model.id}' must not have 'model' field "
                    f"(reserved for EmbeddingModel)"
                )
    
    def _validate_prompts(
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
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
        self, 
        spec: QTypeSpec, 
        registry: ComponentRegistry
    ) -> None:
        """Detect circular references in flow dependencies."""
        for flow in spec.flows or []:
            self._detect_circular_flow_reference(flow.id, set(), registry)
    
    def _detect_circular_flow_reference(
        self, 
        flow_id: str, 
        visited: Set[str], 
        registry: ComponentRegistry
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
