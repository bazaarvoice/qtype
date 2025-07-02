"""
Semantic IR resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation (IR) equivalents, where all ID references
are resolved to actual object references.
"""

from typing import Any, Dict, List, Optional, Union

import qtype.dsl.model as dsl
import qtype.ir.model as ir


class IRResolutionError(Exception):
    """Raised when there's an error during IR resolution."""

    pass


def resolve_semantic_ir(dsl_spec: dsl.QTypeSpec) -> ir.QTypeSpec:
    """
    Transform a DSL QTypeSpec into its semantic intermediate representation.

    This function resolves all ID references in the DSL spec to actual object
    references in the IR spec, creating a fully resolved semantic
    representation.

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
    ir_variables = _resolve_variables(dsl_spec.variables or [])
    ir_prompts = _resolve_prompts(
        dsl_spec.prompts or [], ir_variables
    )

    ir_auth = list(
        dsl_spec.auth or []
    )  # AuthorizationProvider is imported directly

    ir_tools = _resolve_tools(lookup_maps["tools"], ir_variables)

    ir_tool_providers = _resolve_tool_providers(dsl_spec.tool_providers or [], lookup_maps, ir_tools)
    ir_memory = _resolve_memory(dsl_spec.memory or [], ir_models)
    ir_feedback = _resolve_feedback(dsl_spec.feedback or [], ir_prompts)
    ir_agents = _resolve_agents(
        dsl_spec.agents or [], ir_models, ir_prompts, ir_tool_providers, ir_variables
    )
    ir_flows = _resolve_flows(
        dsl_spec.flows or [],
        ir_variables,
        ir_agents,
        ir_models,
        ir_tool_providers,
        ir_memory,
    )
    ir_telemetry = _resolve_telemetry(dsl_spec.telemetry or [], ir_auth)

    return ir.QTypeSpec(
        version=dsl_spec.version,
        models=ir_models if ir_models else None,
        variables=ir_variables if ir_variables else None,
        prompts=ir_prompts if ir_prompts else None,
        tools_provider=ir_tool_providers if ir_tool_providers else None,
        flows=ir_flows if ir_flows else None,
        agents=ir_agents if ir_agents else None,
        feedback=ir_feedback if ir_feedback else None,
        memory=ir_memory if ir_memory else None,
        auth=ir_auth if ir_auth else None,
        telemetry=ir_telemetry if ir_telemetry else None,
    )

def _resolve_tools(tools: Dict[str, dsl.Tool], ir_variables: List[ir.Variable]) -> Dict[str, ir.Tool]:
    """Resolve DSL tools to IR tools."""
    var_map = {var.id: var for var in ir_variables}
    ir_tools = {}
    for tool_id, tool in tools.items():
        # Ensure all inputs and outputs are resolved to Variable objects
        for input_id in tool.inputs:
            if input_id not in var_map:
                raise IRResolutionError(
                    f"Input '{input_id}' not found for tool '{tool_id}'"
                )
        for output_id in tool.outputs:
            if output_id not in var_map:
                raise IRResolutionError(
                    f"Output '{output_id}' not found for tool '{tool_id}'"
                )

        # Convert DSL Tool to IR Tool
        ir_tools[tool_id] = ir.Tool(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            inputs=[var_map[input_id] for input_id in tool.inputs],
            outputs=[var_map[output_id] for output_id in tool.outputs]
        )
    return ir_tools


def _build_lookup_maps(dsl_spec: dsl.QTypeSpec) -> Dict[str, Dict[str, Any]]:
    """Build lookup maps for all objects in the DSL spec."""
    lookup_maps: Dict[str, Dict[str, Any]] = {
        "models": {m.id: m for m in dsl_spec.models or []},
        "variables": {v.id: v for v in dsl_spec.variables or []},
        "prompts": {p.id: p for p in dsl_spec.prompts or []},
        "tools": {},  # Will be populated from tool providers
        "tool_providers": {tp.id: tp for tp in dsl_spec.tool_providers or []},
        "flows": {f.id: f for f in dsl_spec.flows or []},
        "agents": {a.id: a for a in dsl_spec.agents or []},
        "memory": {m.id: m for m in dsl_spec.memory or []},
        "auth": {a.id: a for a in dsl_spec.auth or []},
        "feedback": {f.id: f for f in dsl_spec.feedback or []},
        "telemetry": {t.id: t for t in dsl_spec.telemetry or []},
        "steps": {},  # Will be populated from flows
    }

    # Populate tools from tool providers
    for tp in dsl_spec.tool_providers or []:
        for tool in tp.tools:
            lookup_maps["tools"][tool.id] = tool

    # Populate steps from flows
    for flow in dsl_spec.flows or []:
        for step in flow.steps:
            if isinstance(step, (dsl.Agent, dsl.Tool)):
                lookup_maps["steps"][step.id] = step


    return lookup_maps


def _resolve_models(
    dsl_models: List[dsl.Model], lookup_maps: Dict[str, Dict[str, Any]]
) -> List[ir.Model]:
    """Resolve DSL models to IR models."""
    ir_models: List[ir.Model] = []
    for model in dsl_models:
        if model.dimensions is not None:
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


def _resolve_variables(dsl_inputs: List[dsl.Variable]) -> List[ir.Variable]:
    """Resolve DSL inputs to IR inputs."""
    # Variable objects are imported directly from DSL
    return [ir.Variable(var) for var in dsl_inputs]


def _resolve_prompts(
    dsl_prompts: List[dsl.Prompt],
    ir_variables: List[ir.Variable]
) -> List[ir.Prompt]:
    """Resolve DSL prompts to IR prompts with object references."""
    var_map = {var.id: var for var in ir_variables}

    ir_prompts = []
    for prompt in dsl_prompts:
        # Resolve input variable IDs to Input objects
        resolved_inputs = []
        for input_id in prompt.inputs:
            if input_id not in var_map:
                raise IRResolutionError(
                    f"Input '{input_id}' not found for prompt '{prompt.id}'"
                )
            resolved_inputs.append(var_map[input_id])

        # Resolve output variable IDs to Output objects
        resolved_outputs = []
        for output_id in prompt.outputs or []:
            if output_id not in var_map:
                raise IRResolutionError(
                    f"Output '{output_id}' not found for prompt '{prompt.id}'"
                )
            resolved_outputs.append(var_map[output_id])

        ir_prompts.append(
            ir.Prompt(
                id=prompt.id,
                path=prompt.path,
                template=prompt.template,
                inputs=resolved_inputs,
                outputs=resolved_outputs if resolved_outputs else None,
            )
        )

    return ir_prompts


def _resolve_tool_providers(
    dsl_tool_providers: List[dsl.ToolProvider],
    lookup_maps: Dict[str, Dict[str, Any]],
    ir_tools: Dict[str, ir.Tool]
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

        # make sure all tools in the provider exist in ir_tools
        for tool in tp.tools if tp.tools else []:
            if tool.id not in ir_tools:
                raise IRResolutionError(
                    f"Tool '{tool.id}' not found in ToolProvider '{tp.id}'"
                )
        # Tools are imported directly from DSL
        ir_tool_providers.append(
            ir.ToolProvider(
                id=tp.id,
                name=tp.name,
                tools=[ir_tools[tool.id] for tool in tp.tools],
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


def _resolve_agents(
    dsl_agents: List[dsl.Agent],
    ir_models: List[ir.Model],
    ir_prompts: List[ir.Prompt],
    ir_tool_providers: List[ir.ToolProvider],
    ir_variables: List[ir.Variable]
) -> List[ir.Agent]:
    """Resolve DSL agents to IR agents with object references."""
    model_map = {m.id: m for m in ir_models}
    prompt_map = {p.id: p for p in ir_prompts}
    var_map = {inp.id: inp for inp in ir_variables}
    tool_map = {}
    for tp in ir_tool_providers:
        for tool in tp.tools:
            tool_map[tool.id] = tool

    ir_agents = []
    for agent in dsl_agents:
        # Resolve model
        if agent.model not in model_map:
            raise IRResolutionError(
                f"Model '{agent.model}' not found for agent '{agent.id}'"
            )
        resolved_model = model_map[agent.model]

        # Resolve prompt
        if agent.prompt not in prompt_map:
            raise IRResolutionError(
                f"Prompt '{agent.prompt}' not found for agent '{agent.id}'"
            )
        resolved_prompt = prompt_map[agent.prompt]

        # Resolve inputs
        resolved_inputs = []
        for input_id in agent.inputs or []:
            if input_id not in var_map:
                raise IRResolutionError(
                    f"Input '{input_id}' not found for agent '{agent.id}'"
                )
            resolved_inputs.append(var_map[input_id])

        # Resolve outputs
        resolved_outputs = []
        for output_id in agent.outputs or []:
            if output_id not in var_map:
                raise IRResolutionError(
                    f"Output '{output_id}' not found for agent '{agent.id}'"
                )
            resolved_outputs.append(var_map[output_id])

        # Resolve tools (optional)
        resolved_tools = []
        for tool_id in agent.tools or []:
            if tool_id not in tool_map:
                raise IRResolutionError(
                    f"Tool '{tool_id}' not found for agent '{agent.id}'"
                )
            resolved_tools.append(tool_map[tool_id])

        ir_agents.append(
            ir.Agent(
                id=agent.id,
                inputs=resolved_inputs if resolved_inputs else None,
                outputs=resolved_outputs if resolved_outputs else None,
                model=resolved_model,
                prompt=resolved_prompt,
                tools=resolved_tools if resolved_tools else None,
            )
        )

    return ir_agents


def _resolve_flows(
    dsl_flows: List[dsl.Flow],
    ir_variables: List[ir.Variable],
    ir_agents: List[ir.Agent],
    ir_models: List[ir.Model],
    ir_tool_provider: List[ir.ToolProvider],
    ir_memory: List[ir.Memory],
) -> List[ir.Flow]:
    """Resolve DSL flows to IR flows with object references."""
    var_map = {inp.id: inp for inp in ir_variables}
    agent_map = {a.id: a for a in ir_agents}
    model_map = {m.id: m for m in ir_models}
    tool_map = {}
    for tp in ir_tool_provider:
        for tool in tp.tools:
            tool_map[tool.id] = tool
    memory_map = {m.id: m for m in ir_memory}
    flow_map = {}  # Will be populated as we resolve flows

    ir_flows = []

    # First pass: create flow objects without resolving steps
    for flow in dsl_flows:
        # Resolve inputs
        resolved_inputs = []
        for input_id in flow.inputs or []:
            if input_id not in var_map:
                raise IRResolutionError(
                    f"Input '{input_id}' not found for flow '{flow.id}'"
                )
            resolved_inputs.append(var_map[input_id])

        # Resolve outputs
        resolved_outputs = []
        for output_id in flow.outputs or []:
            if output_id not in var_map:
                raise IRResolutionError(
                    f"Output '{output_id}' not found for flow '{flow.id}'"
                )
            resolved_outputs.append(var_map[output_id])

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
            inputs=resolved_inputs if resolved_inputs else None,
            outputs=resolved_outputs if resolved_outputs else None,
            mode=flow.mode,
            steps=[],  # Will be resolved in second pass
            conditions=None,  # Will be resolved in second pass
            memory=resolved_memory if resolved_memory else None,
        )

        ir_flows.append(ir_flow)
        flow_map[flow.id] = ir_flow

    # Combine the agent and tool maps into a step map
    step_map = {**agent_map, **tool_map}

    # Second pass: resolve steps and conditions
    for i, flow in enumerate(dsl_flows):
        ir_flow = ir_flows[i]

        # Resolve steps
        resolved_steps: List[ir.Step] = []
        for step in flow.steps:
            if isinstance(step, str):
                # Flow reference
                if step not in step_map:
                    raise IRResolutionError(f"Flow '{step}' not found")
                resolved_steps.append(step_map[step])
            elif isinstance(step, dsl.Agent):
                if step.id not in agent_map:
                    raise IRResolutionError(f"Agent '{step.id}' not found")
                resolved_steps.append(agent_map[step.id])
            elif isinstance(step, dsl.Tool):
                if step.id not in tool_map:
                    raise IRResolutionError(f"Tool '{step.id}' not found")
                resolved_steps.append(tool_map[step.id])
            elif isinstance(step, dsl.VectorDBRetriever):
                if step.embedding_model not in model_map:
                    raise IRResolutionError(
                        f"Embedding model '{step.embedding_model}' not found for retriever '{step.id}'"
                    )
                model = model_map[step.embedding_model]

                # look up inputs and outputs in the variable map
                resolved_inputs = []
                for input_id in step.inputs or []:
                    if input_id not in var_map:
                        raise IRResolutionError(
                            f"Input '{input_id}' not found for retriever '{step.id}'"
                        )
                    resolved_inputs.append(var_map[input_id])
                resolved_outputs = []
                for output_id in step.outputs or []:
                    if output_id not in var_map:
                        raise IRResolutionError(
                            f"Output '{output_id}' not found for retriever '{step.id}'"
                        )
                    resolved_outputs.append(var_map[output_id])

                resolved_steps.append(
                    ir.VectorDBRetriever(
                        id=step.id,
                        index=step.index,
                        embedding_model=model, # type: ignore
                        top_k=step.top_k,
                        inputs=resolved_inputs,
                        outputs=resolved_outputs, 
                        args=step.args or {},
                    )
                )
            else:
                raise IRResolutionError(f"Unknown step type: {type(step)}")

        ir_flow.steps = resolved_steps

        # Resolve conditions
        if flow.conditions:
            resolved_conditions = []
            for condition in flow.conditions:
                resolved_then: List[ir.Step] = []
                for step_id in condition.then:
                    # Find step in current flow or reference to another flow
                    step_found = False
                    for resolved_step in resolved_steps:
                        if (
                            hasattr(resolved_step, "id")
                            and resolved_step.id == step_id
                        ):
                            resolved_then.append(resolved_step)
                            step_found = True
                            break
                    if not step_found and step_id in flow_map:
                        resolved_then.append(flow_map[step_id])
                        step_found = True
                    if not step_found:
                        raise IRResolutionError(
                            f"Step or flow '{step_id}' not found for condition"
                        )

                resolved_else: List[ir.Step] = []
                for step_id in condition.else_ or []:
                    step_found = False
                    for resolved_step in resolved_steps:
                        if (
                            hasattr(resolved_step, "id")
                            and resolved_step.id == step_id
                        ):
                            resolved_else.append(resolved_step)
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
                        **{"else": resolved_else if resolved_else else None},
                    )
                )

            ir_flow.conditions = resolved_conditions

    return ir_flows


def _resolve_telemetry(
    dsl_telemetry: List[dsl.TelemetrySink],
    ir_auth: List[dsl.AuthorizationProvider],
) -> List[ir.TelemetrySink]:
    """Resolve DSL telemetry sinks to IR telemetry sinks."""
    ir_telemetry_sinks = []

    # Build auth lookup map
    auth_lookup = {auth.id: auth for auth in ir_auth}

    for telemetry_sink in dsl_telemetry:
        # Resolve auth reference
        auth_obj = None
        if telemetry_sink.auth:
            if telemetry_sink.auth not in auth_lookup:
                raise IRResolutionError(
                    f"Auth provider '{telemetry_sink.auth}' not found"
                )
            auth_obj = auth_lookup[telemetry_sink.auth]

        ir_telemetry_sinks.append(
            ir.TelemetrySink(
                id=telemetry_sink.id,
                endpoint=telemetry_sink.endpoint,
                auth=auth_obj,
            )
        )

    return ir_telemetry_sinks
