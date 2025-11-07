"""
Mermaid diagram generator for QType semantic models.

This module generates Mermaid flowchart diagrams from QType Application and Flow
definitions, providing visual representation of application structure and flow execution.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from qtype.dsl.model import Index
from qtype.semantic.model import (
    Agent,
    APITool,
    Application,
    AuthorizationProvider,
    Decoder,
    DocumentIndex,
    DocumentSearch,
    Flow,
    LLMInference,
    Memory,
    Model,
    PromptTemplate,
    PythonFunctionTool,
    Search,
    Step,
    TelemetrySink,
    Tool,
    VectorIndex,
    VectorSearch,
)


def visualize_application(app: Application) -> str:
    """
    Generate a Mermaid diagram for a complete QType Application.

    Args:
        app: The Application semantic model to visualize

    Returns:
        Complete Mermaid diagram as a string
    """
    lines = [
        "flowchart TD",
        f'    subgraph APP ["📱 Application: {app.id}"]',
        "        direction TB",
        "",
    ]

    # Add flows first (main content)
    flow_connections = []
    for i, flow in enumerate(app.flows):
        flow_diagram, connections = _generate_flow_subgraph(flow, f"FLOW_{i}")
        lines.extend(flow_diagram)
        flow_connections.extend(connections)
        lines.append("")  # Add spacing between flows

    # Add shared resources (models, indexes, etc.)
    shared_resources = _generate_shared_resources(app)
    if shared_resources:
        lines.extend(shared_resources)
        lines.append("")

    # Add telemetry if present
    if app.telemetry:
        lines.extend(_generate_telemetry_nodes(app.telemetry))
        lines.append("")

    lines.append("    end")
    lines.append("")

    # Add connections between flows and external resources
    lines.extend(flow_connections)

    # Add telemetry connections if present
    if app.telemetry:
        for i, flow in enumerate(app.flows):
            for j, step in enumerate(flow.steps):
                if isinstance(step, LLMInference):
                    lines.append(f"    FLOW_{i}_S{j} -.->|traces| TEL_SINK")

    # Add styling for better aesthetics
    lines.extend(_generate_styling())

    return "\n".join(lines)


def visualize_flow(flow: Flow) -> str:
    """
    Generate a Mermaid diagram for a single Flow.

    Args:
        flow: The Flow semantic model to visualize

    Returns:
        Mermaid diagram as a string
    """
    lines = [
        "```mermaid",
        "flowchart LR",
    ]

    flow_diagram, connections = _generate_flow_subgraph(flow, "MAIN")
    lines.extend(flow_diagram)
    lines.extend(connections)

    lines.append("```")
    return "\n".join(lines)


def _generate_flow_subgraph(
    flow: Flow, flow_id: str
) -> tuple[list[str], list[str]]:
    """Generate a flow subgraph with internal nodes and return external connections."""
    # Add more spacing and line breaks for better SVG rendering
    description = f"\n{flow.description}" if flow.description else ""

    # Choose direction based on flow characteristics:
    # - Flows with interface (e.g., Conversational) use LR (left-right)
    # - Linear pipelines without interface use TB (top-bottom)
    direction = "LR" if flow.interface else "TB"

    lines = [
        f'    subgraph {flow_id} ["🔄 Flow: {flow.id}{description}"]',
        f"        direction {direction}",
    ]

    # Generate nodes for each step
    step_nodes = []
    external_connections = []

    # Add start node if flow has inputs
    start_node_id = None
    if flow.inputs:
        start_node_id = f"{flow_id}_START"
        lines.append(
            f'        {start_node_id}@{{shape: circle, label: "▶️ Start"}}'
        )

    for i, step in enumerate(flow.steps):
        node_id = f"{flow_id}_S{i}"
        node_def, ext_conn = _generate_step_node(step, node_id, flow_id)
        step_nodes.append((node_id, step))
        lines.extend(node_def)
        external_connections.extend(ext_conn)

    # Connect steps based on input/output variables
    step_connections = _generate_step_connections(
        step_nodes, flow_id, start_node_id, flow.inputs
    )
    lines.extend(step_connections)

    lines.append("    end")

    return lines, external_connections


def _generate_step_node(
    step: Step, node_id: str, flow_id: str
) -> tuple[list[str], list[str]]:
    """Generate node definition for a step and return external connections."""
    lines = []
    external_connections = []

    if isinstance(step, Flow):
        # Nested flow
        lines.append(
            f'        {node_id}@{{shape: subproc, label: "📋 Flow: {step.id}"}}'
        )
    elif isinstance(step, Agent):
        # Agent with tools
        lines.append(
            f'        {node_id}@{{shape: hex, label: "🤖 Agent: {step.id}"}}'
        )
        # Connect to tools
        for tool in step.tools:
            tool_id = f"TOOL_{_sanitize_id(tool.id)}"
            external_connections.append(f"    {node_id} -.-> {tool_id}")
    elif isinstance(step, LLMInference):
        lines.append(
            f'        {node_id}@{{shape: rounded, label: "✨ {step.id}"}}'
        )
        # Connect to model
        model_id = f"MODEL_{_sanitize_id(step.model.id)}"
        external_connections.append(f"    {node_id} -.->|uses| {model_id}")
        # Connect to memory if present
        if step.memory:
            memory_id = f"MEM_{_sanitize_id(step.memory.id)}"
            external_connections.append(
                f"    {node_id} -.->|stores| {memory_id}"
            )
    elif isinstance(step, PromptTemplate):
        lines.append(
            f'        {node_id}@{{shape: doc, label: "📄 Template: {step.id}"}}'
        )
    elif isinstance(step, Decoder):
        format_label = (
            step.format.value
            if hasattr(step.format, "value")
            else str(step.format)
        )
        lines.append(
            f'        {node_id}@{{shape: lean-r, label: "🔍 Decode: {step.id} ({format_label})"}}'
        )
    elif isinstance(step, VectorSearch):
        lines.append(
            f'        {node_id}@{{shape: cyl, label: "🔎 Vector Search: {step.id}"}}'
        )
        index_id = f"INDEX_{_sanitize_id(step.index.id)}"
        external_connections.append(f"    {node_id} -.-> {index_id}")
    elif isinstance(step, DocumentSearch):
        lines.append(
            f'        {node_id}@{{shape: cyl, label: "📚 Doc Search: {step.id}"}}'
        )
        index_id = f"INDEX_{_sanitize_id(step.index.id)}"
        external_connections.append(f"    {node_id} -.-> {index_id}")
    elif isinstance(step, Search):
        lines.append(
            f'        {node_id}@{{shape: cyl, label: "🔍 Search: {step.id}"}}'
        )
        index_id = f"INDEX_{_sanitize_id(step.index.id)}"
        external_connections.append(f"    {node_id} -.-> {index_id}")
    elif isinstance(step, APITool):
        method_label = step.method.upper()
        lines.append(
            f'        {node_id}["⚡ API: {step.id} ({method_label})"]'
        )
        if step.auth:
            auth_id = f"AUTH_{_sanitize_id(step.auth.id)}"
            external_connections.append(f"    {node_id} -.-> {auth_id}")
    elif isinstance(step, PythonFunctionTool):
        lines.append(
            f'        {node_id}@{{shape: rect, label: "🐍 Python: {step.id} {step.function_name}"}}'
        )
    elif isinstance(step, Tool):
        lines.append(
            f'        {node_id}@{{shape: rect, label: "🔧 Tool: {step.id}"}}'
        )
    else:
        # Generic step
        lines.append(
            f'        {node_id}@{{shape: rect, label: "⚙️ Step: {step.id}"}}'
        )

    return lines, external_connections


def _generate_step_connections(
    step_nodes: list[tuple[str, Step]],
    flow_id: str,
    start_node_id: str | None = None,
    flow_inputs: list[Any] | None = None,
) -> list[str]:
    """Generate connections between steps based on variable flow."""
    lines = []

    # If we have a start node and flow inputs, add them to initial output map
    output_map: dict[str, str] = {}
    if start_node_id and flow_inputs:
        for flow_input in flow_inputs:
            output_map[flow_input.id] = start_node_id

    # Process each step: connect inputs, then register outputs
    # This ensures we connect to the previous producer before updating map
    for node_id, step in step_nodes:
        # First, connect this step's inputs to their producers
        for input_var in step.inputs:
            if input_var.id in output_map:
                producer_id = output_map[input_var.id]
                # Skip self-referencing connections (when a step both
                # consumes and produces the same variable)
                if producer_id == node_id:
                    continue
                # Get a simple string representation of the variable type
                var_type = str(input_var.type).split(".")[
                    -1
                ]  # Get the last part after dots
                var_id_and_type = f"{input_var.id}: {var_type}"

                is_list = str(var_type).startswith("list[") and str(
                    var_type
                ).endswith("]")
                if is_list:
                    var_id_and_type = f'"{var_id_and_type}"'

                lines.append(
                    f"        {producer_id} -->|{var_id_and_type}| {node_id}"
                )

        # Then, register this step's outputs for future steps
        for output_var in step.outputs:
            output_map[output_var.id] = node_id

    # If no connections were made, create a simple sequential flow
    if not lines and len(step_nodes) > 1:
        for i in range(len(step_nodes) - 1):
            current_id, _ = step_nodes[i]
            next_id, _ = step_nodes[i + 1]
            lines.append(f"        {current_id} --> {next_id}")

    return lines


def _find_shared_resources(
    item: Any,
    models: list[Model],
    indexes: list[Index],
    auths: list[AuthorizationProvider],
    memories: list[Memory],
    tools: list[Tool],
) -> None:
    """Find and add shared resources from a step to the provided lists."""
    if isinstance(item, Model):
        models.append(item)
    elif isinstance(item, Index):
        indexes.append(item)
    elif isinstance(item, AuthorizationProvider):
        auths.append(item)
    elif isinstance(item, Memory):
        memories.append(item)
    elif isinstance(item, Tool):
        tools.append(item)
    if isinstance(item, BaseModel):
        # iterate over all fields in the BaseModel
        for field_name in item.__pydantic_fields__.keys():
            value = getattr(item, field_name)
            if isinstance(value, list):
                for sub_item in value:
                    _find_shared_resources(
                        sub_item, models, indexes, auths, memories, tools
                    )
            elif isinstance(value, dict):
                for sub_item in value.values():
                    _find_shared_resources(
                        sub_item, models, indexes, auths, memories, tools
                    )
            else:
                _find_shared_resources(
                    value, models, indexes, auths, memories, tools
                )
    # end recursion for non-model items


def _generate_shared_resources(app: Application) -> list[str]:
    """Generate nodes for shared resources (models, indexes, auths, memories)."""
    lines = []

    models: list[Model] = []
    indexes: list[Index] = []
    auths: list[AuthorizationProvider] = []
    memories: list[Memory] = []
    tools: list[Tool] = []

    _find_shared_resources(app, models, indexes, auths, memories, tools)

    # Ensure we have unique resources
    models = list(set(models))
    indexes = list(set(indexes))
    auths = list(set(auths))
    memories = list(set(memories))
    tools = list(set(tools))

    if models or indexes or auths or memories or tools:
        lines.append('    subgraph RESOURCES ["🔧 Shared Resources"]')
        lines.append("        direction LR")

        # Authorization Providers (show first as they're referenced by others)
        for auth in auths:
            auth_id = f"AUTH_{_sanitize_id(auth.id)}"
            auth_type = auth.type.upper()
            lines.append(
                f'        {auth_id}@{{shape: hex, label: "🔐 {auth.id}\\n{auth_type}"}}'
            )

        # Models
        for model in models:
            model_id = f"MODEL_{_sanitize_id(model.id)}"
            provider_label = model.provider
            lines.append(
                f'        {model_id}@{{shape: rounded, label: "✨ {model.id} ({provider_label})" }}'
            )

            if model.auth:
                auth_id = f"AUTH_{_sanitize_id(model.auth.id)}"
                lines.append(f"        {model_id} -.->|uses| {auth_id}")

        # Indexes
        for index in indexes:
            index_id = f"INDEX_{_sanitize_id(index.id)}"
            if isinstance(index, VectorIndex):
                lines.append(
                    f'        {index_id}@{{shape: cyl, label: "🗂️ Vector: {index.id}"}}'
                )
                # Connect to embedding model
                emb_model_id = f"EMB_{_sanitize_id(index.embedding_model.id)}"
                lines.append(
                    f'        {emb_model_id}@{{shape: rounded, label: "🎯 {index.embedding_model.id}"}}'
                )
                lines.append(f"        {index_id} -.->|embeds| {emb_model_id}")
            elif isinstance(index, DocumentIndex):
                lines.append(
                    f'        {index_id}@{{shape: cyl, label: "📚 Docs: {index.id}"}}'
                )
            else:
                lines.append(
                    f'        {index_id}@{{shape: cyl, label: "🗂️ {index.id}"}}'
                )

            if index.auth:
                # Handle auth as either AuthorizationProvider object or string ID
                if isinstance(index.auth, str):
                    auth_id = f"AUTH_{_sanitize_id(index.auth)}"
                else:
                    auth_id = f"AUTH_{_sanitize_id(index.auth.id)}"
                lines.append(f"        {index_id} -.->|uses| {auth_id}")

        # Memories
        for memory in memories:
            memory_id = f"MEM_{_sanitize_id(memory.id)}"
            token_limit = (
                f"{memory.token_limit // 1000}K"
                if memory.token_limit >= 1000
                else str(memory.token_limit)
            )
            lines.append(
                f'        {memory_id}@{{shape: win-pane, label: "🧠 {memory.id}\\n{token_limit}T"}}'
            )

        # Tools (if not already covered by flows)
        for tool in tools:
            tool_id = f"TOOL_{_sanitize_id(tool.id)}"
            if isinstance(tool, APITool):
                method_label = tool.method.upper()
                lines.append(
                    f'        {tool_id}["⚡ {tool.id} ({method_label})"]'
                )
                if tool.auth:
                    auth_id = f"AUTH_{_sanitize_id(tool.auth.id)}"
                    lines.append(f"        {tool_id} -.->|uses| {auth_id}")
            elif isinstance(tool, PythonFunctionTool):
                lines.append(
                    f'        {tool_id}@{{shape: rect, label: "🐍 {tool.id}\\n{tool.function_name}"}}'
                )
            else:
                lines.append(
                    f'        {tool_id}@{{shape: rect, label: "🔧 {tool.id}"}}'
                )

        lines.append("    end")

    return lines


def _generate_telemetry_nodes(telemetry: TelemetrySink) -> list[str]:
    """Generate nodes for telemetry configuration."""
    # Replace :// with a space to avoid markdown link parsing
    safe_endpoint = telemetry.endpoint.replace("://", "&colon;//")

    lines = [
        '    subgraph TELEMETRY ["📊 Observability"]',
        "        direction TB",
        f'        TEL_SINK@{{shape: curv-trap, label: "📡 {telemetry.id}\\n{safe_endpoint}"}}',
    ]

    if telemetry.auth:
        auth_id = f"AUTH_{_sanitize_id(telemetry.auth.id)}"
        lines.append(f"        TEL_SINK -.->|uses| {auth_id}")

    lines.append("    end")
    return lines


def _sanitize_id(id_str: str) -> str:
    """Sanitize ID strings for use in Mermaid diagrams."""
    return id_str.replace("-", "_").replace(".", "_").replace(" ", "_").upper()


def _generate_styling() -> list[str]:
    """Generate CSS styling for the Mermaid diagram."""
    return [
        "",
        "    %% Styling",
        "    classDef appBox fill:none,stroke:#495057,stroke-width:3px",
        "    classDef flowBox fill:#e1f5fe,stroke:#0277bd,stroke-width:2px",
        "    classDef llmNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
        "    classDef modelNode fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px",
        "    classDef authNode fill:#fff3e0,stroke:#ef6c00,stroke-width:2px",
        "    classDef telemetryNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px",
        "    classDef resourceBox fill:#f5f5f5,stroke:#616161,stroke-width:1px",
        "",
        "    class APP appBox",
        "    class FLOW_0 flowBox",
        "    class RESOURCES resourceBox",
        "    class TELEMETRY telemetryNode",
    ]
