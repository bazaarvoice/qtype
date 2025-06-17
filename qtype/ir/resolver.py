"""
Semantic IR resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation (IR) equivalents, where all ID references
are resolved to actual object references.
"""

from typing import Any, Dict, List

import qtype.dsl.models as dsl
import qtype.ir.models as ir


class IRResolutionError(Exception):
    """Raised when there's an error during IR resolution."""

    pass


def resolve_semantic_ir(dsl_spec: dsl.QTypeSpec) -> ir.QTypeSpec:
    """
    Transform a DSL QTypeSpec into its semantic intermediate representation.

    This function resolves all ID references in the DSL spec to actual object
    references in the IR spec, creating a fully resolved semantic representation.

    Args:
        dsl_spec: The DSL QTypeSpec to transform

    Returns:
        ir.QTypeSpec: The resolved IR specification

    Raises:
        IRResolutionError: If any required references cannot be resolved
    """
    # Create lookup maps for all objects by ID
    lookup_maps = _build_lookup_maps(dsl_spec)

    # Resolve each component type
    ir_models = _resolve_models(dsl_spec.models or [], lookup_maps)
    ir_inputs = _resolve_inputs(dsl_spec.inputs or [])
    ir_outputs = _resolve_outputs(dsl_spec.prompts or [], dsl_spec.flows or [])
    ir_prompts = _resolve_prompts(
        dsl_spec.prompts or [], ir_inputs, ir_outputs
    )
    ir_retrievers = _resolve_retrievers(dsl_spec.retrievers or [], ir_models)

    # Second pass to resolve SearchRetriever query_prompt references
    _resolve_retriever_prompts(
        ir_retrievers, ir_prompts, dsl_spec.retrievers or []
    )

    ir_tools = _resolve_tool_providers(dsl_spec.tools or [], lookup_maps)
    ir_memory = _resolve_memory(dsl_spec.memory or [], ir_models)
    ir_feedback = _resolve_feedback(dsl_spec.feedback or [], ir_prompts)
    ir_flows = _resolve_flows(
        dsl_spec.flows or [],
        ir_inputs,
        ir_outputs,
        ir_prompts,
        ir_tools,
        ir_retrievers,
        ir_memory,
    )
    ir_auth = list(
        dsl_spec.auth or []
    )  # AuthorizationProvider is imported directly

    return ir.QTypeSpec(
        version=dsl_spec.version,
        models=ir_models if ir_models else None,
        inputs=ir_inputs if ir_inputs else None,
        prompts=ir_prompts if ir_prompts else None,
        retrievers=ir_retrievers if ir_retrievers else None,
        tools=ir_tools if ir_tools else None,
        flows=ir_flows if ir_flows else None,
        feedback=ir_feedback if ir_feedback else None,
        memory=ir_memory if ir_memory else None,
        auth=ir_auth if ir_auth else None,
    )


def _build_lookup_maps(dsl_spec: dsl.QTypeSpec) -> Dict[str, Dict[str, Any]]:
    """Build lookup maps for all objects in the DSL spec."""
    lookup_maps = {
        "models": {m.id: m for m in dsl_spec.models or []},
        "inputs": {i.id: i for i in dsl_spec.inputs or []},
        "prompts": {p.id: p for p in dsl_spec.prompts or []},
        "retrievers": {r.id: r for r in dsl_spec.retrievers or []},
        "tools": {},  # Will be populated from tool providers
        "tool_providers": {tp.id: tp for tp in dsl_spec.tools or []},
        "flows": {f.id: f for f in dsl_spec.flows or []},
        "memory": {m.id: m for m in dsl_spec.memory or []},
        "auth": {a.id: a for a in dsl_spec.auth or []},
        "feedback": {f.id: f for f in dsl_spec.feedback or []},
        "steps": {},  # Will be populated from flows
        "outputs": {},  # Will be populated from prompts and steps
    }

    # Populate tools from tool providers
    for tp in dsl_spec.tools or []:
        for tool in tp.tools:
            lookup_maps["tools"][tool.id] = tool

    # Populate steps from flows
    for flow in dsl_spec.flows or []:
        for step in flow.steps:
            if isinstance(step, dsl.Step):
                lookup_maps["steps"][step.id] = step

    # Populate outputs from prompts and steps
    for prompt in dsl_spec.prompts or []:
        for output_id in prompt.output_vars or []:
            lookup_maps["outputs"][output_id] = output_id

    for flow in dsl_spec.flows or []:
        for step in flow.steps:
            if isinstance(step, dsl.Step):
                for output_id in step.output_vars or []:
                    lookup_maps["outputs"][output_id] = output_id

    return lookup_maps


def _resolve_models(
    dsl_models: List[dsl.Model], lookup_maps: Dict[str, Dict[str, Any]]
) -> List[ir.Model]:
    """Resolve DSL models to IR models."""
    ir_models = []
    for model in dsl_models:
        if isinstance(model, dsl.EmbeddingModel):
            ir_models.append(
                ir.EmbeddingModel(
                    id=model.id,
                    provider=model.provider,
                    model_id=model.model_id,
                    inference_params=model.inference_params,
                    dimensions=model.dimensions,
                )
            )
        else:
            ir_models.append(
                ir.Model(
                    id=model.id,
                    provider=model.provider,
                    model_id=model.model_id,
                    inference_params=model.inference_params,
                )
            )
    return ir_models


def _resolve_inputs(dsl_inputs: List[dsl.Input]) -> List[ir.Input]:
    """Resolve DSL inputs to IR inputs."""
    # Input objects are imported directly from DSL
    return list(dsl_inputs)


def _resolve_outputs(
    dsl_prompts: List[dsl.Prompt], dsl_flows: List[dsl.Flow]
) -> List[ir.Output]:
    """Create output objects from prompt and step output variable IDs."""
    outputs = []
    output_ids = set()

    # Collect output IDs from prompts
    for prompt in dsl_prompts:
        for output_id in prompt.output_vars or []:
            if output_id not in output_ids:
                outputs.append(
                    ir.Output(
                        id=output_id,
                        type=dsl.VariableType.text,  # Default to text, could be inferred
                    )
                )
                output_ids.add(output_id)

    # Collect output IDs from flow steps
    for flow in dsl_flows:
        for step in flow.steps:
            if isinstance(step, dsl.Step):
                for output_id in step.output_vars or []:
                    if output_id not in output_ids:
                        outputs.append(
                            ir.Output(
                                id=output_id,
                                type=dsl.VariableType.text,  # Default to text
                            )
                        )
                        output_ids.add(output_id)

    return outputs


def _resolve_prompts(
    dsl_prompts: List[dsl.Prompt],
    ir_inputs: List[ir.Input],
    ir_outputs: List[ir.Output],
) -> List[ir.Prompt]:
    """Resolve DSL prompts to IR prompts with object references."""
    input_map = {inp.id: inp for inp in ir_inputs}
    output_map = {out.id: out for out in ir_outputs}

    ir_prompts = []
    for prompt in dsl_prompts:
        # Resolve input variable IDs to Input objects
        resolved_inputs = []
        for input_id in prompt.input_vars:
            if input_id not in input_map:
                raise IRResolutionError(
                    f"Input '{input_id}' not found for prompt '{prompt.id}'"
                )
            resolved_inputs.append(input_map[input_id])

        # Resolve output variable IDs to Output objects
        resolved_outputs = []
        for output_id in prompt.output_vars or []:
            if output_id not in output_map:
                raise IRResolutionError(
                    f"Output '{output_id}' not found for prompt '{prompt.id}'"
                )
            resolved_outputs.append(output_map[output_id])

        ir_prompts.append(
            ir.Prompt(
                id=prompt.id,
                path=prompt.path,
                template=prompt.template,
                input_vars=resolved_inputs,
                output_vars=resolved_outputs if resolved_outputs else None,
            )
        )

    return ir_prompts


def _resolve_retrievers(
    dsl_retrievers: List[dsl.BaseRetriever], ir_models: List[ir.Model]
) -> List[ir.BaseRetriever]:
    """Resolve DSL retrievers to IR retrievers with model object references."""
    model_map = {m.id: m for m in ir_models}

    ir_retrievers = []
    for retriever in dsl_retrievers:
        if isinstance(retriever, dsl.VectorDBRetriever):
            # Find the embedding model
            if retriever.embedding_model not in model_map:
                raise IRResolutionError(
                    f"Embedding model '{retriever.embedding_model}' not found"
                )

            embedding_model = model_map[retriever.embedding_model]
            if not isinstance(embedding_model, ir.EmbeddingModel):
                raise IRResolutionError(
                    f"Model '{retriever.embedding_model}' is not an EmbeddingModel"
                )

            ir_retrievers.append(
                ir.VectorDBRetriever(
                    id=retriever.id,
                    index=retriever.index,
                    embedding_model=embedding_model,
                    top_k=retriever.top_k,
                )
            )
        elif isinstance(retriever, dsl.SearchRetriever):
            # Note: query_prompt will be resolved later if needed
            ir_retrievers.append(
                ir.SearchRetriever(
                    id=retriever.id,
                    index=retriever.index,
                    top_k=retriever.top_k,
                    query_prompt=None,  # Will be resolved in a second pass if needed
                )
            )

    return ir_retrievers


def _resolve_retriever_prompts(
    ir_retrievers: List[ir.BaseRetriever],
    ir_prompts: List[ir.Prompt],
    dsl_retrievers: List[dsl.BaseRetriever],
) -> None:
    """Second pass to resolve SearchRetriever query_prompt references."""
    prompt_map = {p.id: p for p in ir_prompts}

    # Create a mapping from IR retrievers back to DSL retrievers
    dsl_retriever_map = {r.id: r for r in dsl_retrievers}

    for ir_retriever in ir_retrievers:
        if isinstance(ir_retriever, ir.SearchRetriever):
            dsl_retriever = dsl_retriever_map.get(ir_retriever.id)
            if (
                dsl_retriever
                and isinstance(dsl_retriever, dsl.SearchRetriever)
                and dsl_retriever.query_prompt
            ):
                if dsl_retriever.query_prompt not in prompt_map:
                    raise IRResolutionError(
                        f"Query prompt '{dsl_retriever.query_prompt}' not found for retriever '{ir_retriever.id}'"
                    )
                ir_retriever.query_prompt = prompt_map[
                    dsl_retriever.query_prompt
                ]


def _resolve_tool_providers(
    dsl_tool_providers: List[dsl.ToolProvider],
    lookup_maps: Dict[str, Dict[str, Any]],
) -> List[ir.ToolProvider]:
    """Resolve DSL tool providers to IR tool providers."""
    ir_tool_providers = []

    for tp in dsl_tool_providers:
        # Resolve auth reference
        auth_obj = None
        if tp.auth:
            if tp.auth not in lookup_maps["auth"]:
                raise IRResolutionError(f"Auth provider '{tp.auth}' not found")
            auth_obj = lookup_maps["auth"][tp.auth]

        # Tools are imported directly from DSL
        ir_tool_providers.append(
            ir.ToolProvider(
                id=tp.id,
                name=tp.name,
                tools=list(tp.tools),  # Tool objects are imported from DSL
                openapi_spec=tp.openapi_spec,
                include_tags=tp.include_tags,
                exclude_paths=tp.exclude_paths,
                auth=auth_obj,
            )
        )

    return ir_tool_providers


def _resolve_memory(
    dsl_memory: List[dsl.Memory], ir_models: List[ir.Model]
) -> List[ir.Memory]:
    """Resolve DSL memory to IR memory with model object references."""
    model_map = {m.id: m for m in ir_models}

    ir_memory = []
    for mem in dsl_memory:
        if mem.embedding_model not in model_map:
            raise IRResolutionError(
                f"Embedding model '{mem.embedding_model}' not found"
            )

        embedding_model = model_map[mem.embedding_model]
        if not isinstance(embedding_model, ir.EmbeddingModel):
            raise IRResolutionError(
                f"Model '{mem.embedding_model}' is not an EmbeddingModel"
            )

        ir_memory.append(
            ir.Memory(
                id=mem.id,
                type=mem.type,
                embedding_model=embedding_model,
                persist=mem.persist,
                ttl_minutes=mem.ttl_minutes,
                use_for_context=mem.use_for_context,
            )
        )

    return ir_memory


def _resolve_feedback(
    dsl_feedback: List[dsl.Feedback], ir_prompts: List[ir.Prompt]
) -> List[ir.Feedback]:
    """Resolve DSL feedback to IR feedback with prompt object references."""
    prompt_map = {p.id: p for p in ir_prompts}

    ir_feedback = []
    for feedback in dsl_feedback:
        prompt_obj = None
        if feedback.prompt:
            if feedback.prompt not in prompt_map:
                raise IRResolutionError(
                    f"Prompt '{feedback.prompt}' not found for feedback '{feedback.id}'"
                )
            prompt_obj = prompt_map[feedback.prompt]

        ir_feedback.append(
            ir.Feedback(
                id=feedback.id,
                type=feedback.type,
                question=feedback.question,
                prompt=prompt_obj,
            )
        )

    return ir_feedback


def _resolve_flows(
    dsl_flows: List[dsl.Flow],
    ir_inputs: List[ir.Input],
    ir_outputs: List[ir.Output],
    ir_prompts: List[ir.Prompt],
    ir_tools: List[ir.ToolProvider],
    ir_retrievers: List[ir.BaseRetriever],
    ir_memory: List[ir.Memory],
) -> List[ir.Flow]:
    """Resolve DSL flows to IR flows with object references."""
    input_map = {inp.id: inp for inp in ir_inputs}
    output_map = {out.id: out for out in ir_outputs}
    prompt_map = {p.id: p for p in ir_prompts}
    tool_map = {}
    for tp in ir_tools:
        for tool in tp.tools:
            tool_map[tool.id] = tool
    retriever_map = {r.id: r for r in ir_retrievers}
    memory_map = {m.id: m for m in ir_memory}
    flow_map = {}  # Will be populated as we resolve flows

    ir_flows = []

    # First pass: create flow objects without resolving steps
    for flow in dsl_flows:
        # Resolve inputs
        resolved_inputs = []
        for input_id in flow.inputs or []:
            if input_id not in input_map:
                raise IRResolutionError(
                    f"Input '{input_id}' not found for flow '{flow.id}'"
                )
            resolved_inputs.append(input_map[input_id])

        # Resolve outputs
        resolved_outputs = []
        for output_id in flow.outputs or []:
            if output_id not in output_map:
                raise IRResolutionError(
                    f"Output '{output_id}' not found for flow '{flow.id}'"
                )
            resolved_outputs.append(output_map[output_id])

        # Resolve memory
        resolved_memory = []
        for mem_id in flow.memory or []:
            if mem_id not in memory_map:
                raise IRResolutionError(
                    f"Memory '{mem_id}' not found for flow '{flow.id}'"
                )
            resolved_memory.append(memory_map[mem_id])

        ir_flow = ir.Flow(
            id=flow.id,
            mode=flow.mode,
            inputs=resolved_inputs if resolved_inputs else None,
            outputs=resolved_outputs if resolved_outputs else None,
            steps=[],  # Will be resolved in second pass
            conditions=None,  # Will be resolved in second pass
            memory=resolved_memory if resolved_memory else None,
        )

        ir_flows.append(ir_flow)
        flow_map[flow.id] = ir_flow

    # Second pass: resolve steps and conditions
    for i, flow in enumerate(dsl_flows):
        ir_flow = ir_flows[i]

        # Resolve steps
        resolved_steps = []
        for step in flow.steps:
            if isinstance(step, str):
                # Flow reference
                if step not in flow_map:
                    raise IRResolutionError(f"Flow '{step}' not found")
                resolved_steps.append(flow_map[step])
            else:
                # Step object
                resolved_step = _resolve_step(
                    step,
                    input_map,
                    output_map,
                    prompt_map,
                    tool_map,
                    retriever_map,
                    flow_map,
                )
                resolved_steps.append(resolved_step)

        ir_flow.steps = resolved_steps

        # Resolve conditions
        if flow.conditions:
            resolved_conditions = []
            for condition in flow.conditions:
                resolved_then = []
                for step_id in condition.then:
                    # Find step in current flow or reference to another flow
                    step_found = False
                    for step in resolved_steps:
                        if hasattr(step, "id") and step.id == step_id:
                            resolved_then.append(step)
                            step_found = True
                            break
                    if not step_found and step_id in flow_map:
                        resolved_then.append(flow_map[step_id])
                        step_found = True
                    if not step_found:
                        raise IRResolutionError(
                            f"Step or flow '{step_id}' not found for condition"
                        )

                resolved_else = []
                for step_id in condition.else_ or []:
                    step_found = False
                    for step in resolved_steps:
                        if hasattr(step, "id") and step.id == step_id:
                            resolved_else.append(step)
                            step_found = True
                            break
                    if not step_found and step_id in flow_map:
                        resolved_else.append(flow_map[step_id])
                        step_found = True
                    if not step_found:
                        raise IRResolutionError(
                            f"Step or flow '{step_id}' not found for condition"
                        )

                resolved_conditions.append(
                    ir.Condition(
                        if_var=condition.if_var,
                        equals=condition.equals,
                        exists=condition.exists,
                        then=resolved_then,
                        else_=resolved_else if resolved_else else None,
                    )
                )

            ir_flow.conditions = resolved_conditions

    return ir_flows


def _resolve_step(
    dsl_step: dsl.Step,
    input_map: Dict[str, ir.Input],
    output_map: Dict[str, ir.Output],
    prompt_map: Dict[str, ir.Prompt],
    tool_map: Dict[str, ir.Tool],
    retriever_map: Dict[str, ir.BaseRetriever],
    flow_map: Dict[str, ir.Flow],
) -> ir.Step:
    """Resolve a DSL step to an IR step with object references."""
    # Resolve input variables
    resolved_inputs = []
    for input_id in dsl_step.input_vars or []:
        if input_id not in input_map:
            raise IRResolutionError(
                f"Input '{input_id}' not found for step '{dsl_step.id}'"
            )
        resolved_inputs.append(input_map[input_id])

    # Resolve output variables
    resolved_outputs = []
    for output_id in dsl_step.output_vars or []:
        if output_id not in output_map:
            raise IRResolutionError(
                f"Output '{output_id}' not found for step '{dsl_step.id}'"
            )
        resolved_outputs.append(output_map[output_id])

    # Resolve component
    component_obj = None
    if dsl_step.component:
        # Check in each component type
        if dsl_step.component in prompt_map:
            component_obj = prompt_map[dsl_step.component]
        elif dsl_step.component in tool_map:
            component_obj = tool_map[dsl_step.component]
        elif dsl_step.component in retriever_map:
            component_obj = retriever_map[dsl_step.component]
        elif dsl_step.component in flow_map:
            component_obj = flow_map[dsl_step.component]
        else:
            raise IRResolutionError(
                f"Component '{dsl_step.component}' not found for step '{dsl_step.id}'"
            )

    return ir.Step(
        id=dsl_step.id,
        input_vars=resolved_inputs if resolved_inputs else None,
        output_vars=resolved_outputs if resolved_outputs else None,
        component=component_obj,
    )
