"""
Intermediate Representation (IR) resolution logic for QType.
"""
from typing import Any, Dict, List, Set

from qtype.dsl.models import (
    EmbeddingModel,
    QTypeSpec,
    Step,
)

class SemanticValidationError(Exception):
    """
    Custom exception for semantic validation errors in QType specifications.
    Contains a list of error messages.
    """
    def __init__(self, errors: List[str]) -> None:
        super().__init__("Semantic validation failed")
        self.errors = errors

    def __str__(self) -> str:
        return "\n".join(self.errors)

def validate_semantics(spec: QTypeSpec) -> None:
    """
    Validate a QTypeSpec object for IR consistency and correctness.

    Args:
        spec (QTypeSpec): The QType specification to validate.

    Raises:
        ValidationError: If any validation errors are found.
    """
    errors: List[str] = []
    id_maps: Dict[str, Dict[str, Any]] = _collect_ids(spec, errors)
    _check_unique_ids(id_maps, errors)
    _check_referential_integrity(spec, id_maps, errors)
    _check_flows(spec, id_maps, errors)
    _check_memory_vs_retriever(spec, id_maps, errors)
    _check_tooling_rules(spec, id_maps, errors)
    _check_model_embedding_rules(spec, id_maps, errors)
    _check_prompt_requirements(spec, id_maps, errors)
    _check_circular_flows(spec, id_maps, errors)
    if errors:
        raise SemanticValidationError(errors)


def _collect_ids(spec: QTypeSpec, errors: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Collect all IDs from the QTypeSpec for referential integrity checks.
    """
    id_maps: Dict[str, Dict[str, Any]] = {
        "model": {m.id: m for m in spec.models or []},
        "input": {i.id: i for i in spec.inputs or []},
        "prompt": {p.id: p for p in spec.prompts or []},
        "output": {},
        "memory": {m.id: m for m in spec.memory or []},
        "toolprovider": {tp.id: tp for tp in spec.tools or []},
        "auth": {a.id: a for a in spec.auth or []},
        "feedback": {f.id: f for f in spec.feedback or []},
        "retriever": {r.id: r for r in spec.retrievers or []},
        "flow": {f.id: f for f in spec.flows or []},
        "step": {},
        "tool": {},
    }
    for tp in spec.tools or []:
        for t in tp.tools or []:
            if t.id in id_maps["tool"]:
                errors.append(f"Duplicate Tool.id: {t.id}")
            id_maps["tool"][t.id] = t
    for p in spec.prompts or []:
        for outvar in p.output_vars or []:
            id_maps["output"][outvar] = None
    for f in spec.flows or []:
        id_maps["flow"][f.id] = f
        for s in f.steps:
            if isinstance(s, Step):
                if s.id in id_maps["step"]:
                    errors.append(f"Duplicate Step.id: {s.id}")
                id_maps["step"][s.id] = s
    # Collect all output variables from steps
    for s in id_maps["step"].values():
        for outvar in s.output_vars or []:
            if outvar in id_maps["output"]:
                errors.append(f"Duplicate Output.id: {outvar}")
            id_maps["output"][outvar] = None
    return id_maps


def _check_unique_ids(id_maps: Dict[str, Dict[str, Any]], errors: List[str]) -> None:
    """
    Ensure all IDs are unique within their respective categories.
    """
    for k, idmap in id_maps.items():
        seen: Set[str] = set()
        for id_ in idmap:
            if id_ in seen:
                errors.append(f"Duplicate {k.capitalize()}.id: {id_}")
            seen.add(id_)


def _check_referential_integrity(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Check that all references in the spec point to valid IDs.
    """
    for p in spec.prompts or []:
        for var in p.input_vars:
            if var not in id_maps["input"]:
                errors.append(f"Prompt {p.id} input_var {var} not found in Input.id")
        for var in p.output_vars or []:
            if var not in id_maps["output"]:
                errors.append(f"Prompt {p.id} output_var {var} not found in Output.id")
    
    for f in spec.flows or []:
        for s in f.steps:
            if isinstance(s, Step):
                # Check if component exists in any of the valid component types
                component_found = False
                component_types = ["prompt", "tool", "flow", "retriever"]
                
                for component_type in component_types:
                    if s.component in id_maps[component_type]:
                        component_found = True
                        break
                
                if not component_found:
                    valid_types = ", ".join(component_types)
                    errors.append(
                        f"Step {s.id} component {s.component} not found in any valid component type ({valid_types})"
                    )
                
                for var in s.input_vars or []:
                    if var not in id_maps["input"]:
                        errors.append(
                            f"Step {s.id} input_var {var} not found in Input.id"
                        )
                for var in s.output_vars or []:
                    if var not in id_maps["output"]:
                        errors.append(
                            f"Step {s.id} output_var {var} not found in Output.id"
                        )
    
    for r in id_maps["retriever"].values():
        if hasattr(r, "embedding_model") and r.embedding_model.id not in id_maps["model"]:
            errors.append(
                f"Retriever {r.id} embedding_model {r.embedding_model} not found in Model.id"
            )
        # Confirm the embedding_model is an instance of EmbeddingModel
        if hasattr(r, "embedding_model") and not isinstance(
            r.embedding_model, EmbeddingModel
        ):
            errors.append(
                f"Retriever {r.id} embedding_model {r.embedding_model} must be an instance of EmbeddingModel"
            )
    
    for m in spec.memory or []:
        if m.embedding_model not in id_maps["model"]:
            errors.append(
                f"Memory {m.id} embedding_model {m.embedding_model} not found in Model.id"
            )
    
    for tp in spec.tools or []:
        if tp.auth and tp.auth not in id_maps["auth"]:
            errors.append(
                f"ToolProvider {tp.id} auth {tp.auth} not found in AuthorizationProvider.id"
            )
    
    for f in spec.flows or []:
        for mem in f.memory or []:
            if mem not in id_maps["memory"]:
                errors.append(f"Flow {f.id} memory {mem} not found in Memory.id")


def _check_flows(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Validate flow structure, step references, and flow-specific rules.
    """
    for f in spec.flows or []:
        step_ids: Set[str] = set()
        for s in f.steps:
            if isinstance(s, Step):
                if s.id in step_ids:
                    errors.append(f"Duplicate Step.id {s.id} in Flow {f.id}")
                step_ids.add(s.id)
            elif isinstance(s, str):
                if s not in id_maps["flow"]:
                    errors.append(
                        f"Flow {f.id} steps[] string {s} not found in Flow.id"
                    )
        for var in f.inputs or []:
            if var not in id_maps["input"]:
                errors.append(f"Flow {f.id} input {var} not found in Input.id")
        for var in f.outputs or []:
            if var not in id_maps["output"]:
                errors.append(f"Flow {f.id} output {var} not found in Output.id")
        for cond in f.conditions or []:
            for then_id in cond.then:
                if then_id not in step_ids and then_id not in id_maps["flow"]:
                    errors.append(
                        f"Flow {f.id} condition then[] {then_id} not found in Step.id or Flow.id"
                    )
            for else_id in cond.else_ or []:
                if else_id not in step_ids and else_id not in id_maps["flow"]:
                    errors.append(
                        f"Flow {f.id} condition else_[] {else_id} not found in Step.id or Flow.id"
                    )
        if f.mode == "chat":
            if not f.memory:
                errors.append(f"Flow {f.id} mode=chat must set memory[]")
        else:
            if f.memory:
                errors.append(f"Flow {f.id} mode!=chat must not set memory[]")


def _check_memory_vs_retriever(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Ensure Memory IDs are not used as Step components in flows.
    """
    mem_ids: Set[str] = {m.id for m in spec.memory or []}
    for f in spec.flows or []:
        for s in f.steps:
            if isinstance(s, Step) and s.component in mem_ids:
                errors.append(
                    f"Memory.id {s.component} used as Step.component in Flow {f.id}"
                )


def _check_tooling_rules(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Validate ToolProvider and Tool rules for uniqueness and schema requirements.
    """
    for tp in spec.tools or []:
        tool_names: Set[str] = set()
        tool_ids: Set[str] = set()
        for t in tp.tools or []:
            if t.id in tool_ids:
                errors.append(f"Duplicate Tool.id {t.id} in ToolProvider {tp.id}")
            tool_ids.add(t.id)
            if t.name in tool_names:
                errors.append(f"Duplicate Tool.name {t.name} in ToolProvider {tp.id}")
            tool_names.add(t.name)
            if not t.input_schema or not t.output_schema:
                errors.append(
                    f"Tool {t.id} in ToolProvider {tp.id} missing input_schema or output_schema"
                )


def _check_model_embedding_rules(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Validate consistency between Model and EmbeddingModel providers and fields.
    """
    model_providers = {m.provider for m in spec.models or []}
    # No need to check for EmbeddingModel separately, just use model ids
    for m in spec.models or []:
        if isinstance(m, EmbeddingModel) and hasattr(m, "inference_params"):
            errors.append(f"EmbeddingModel {m.id} must not have inference_params")
        if hasattr(m, "model"):
            errors.append(
                f"Model {m.id} must not have 'model' field (reserved for EmbeddingModel)"
            )


def _check_prompt_requirements(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Ensure each Prompt defines either a template or a path, but not both.
    """
    for p in spec.prompts or []:
        if (p.template is None and p.path is None) or (p.template and p.path):
            errors.append(
                f"Prompt {p.id} must define either template or path, but not both"
            )
        for var in p.input_vars:
            if var not in id_maps["input"]:
                errors.append(f"Prompt {p.id} input_var {var} not found in Input.id")
        for var in p.output_vars or []:
            if var not in id_maps["output"]:
                errors.append(f"Prompt {p.id} output_var {var} not found in Output.id")


def _check_circular_flows(
    spec: QTypeSpec, id_maps: Dict[str, Dict[str, Any]], errors: List[str]
) -> None:
    """
    Detect circular references in flows.
    """
    def visit(flow_id: str, seen: Set[str]) -> None:
        if flow_id in seen:
            errors.append(f"Circular reference detected in Flow {flow_id}")
            return
        seen.add(flow_id)
        flow = id_maps["flow"].get(flow_id)
        if not flow:
            return
        for s in flow.steps:
            if isinstance(s, str):
                visit(s, seen.copy())

    for f in spec.flows or []:
        visit(f.id, set())
