from qtype.dsl.model import (
    OpenAPIToolProvider,
    PythonModuleToolProvider,
    Tool,
    ToolProviderType,
)
from tool_provider_python_module import load_python_module_tools


def load_tools(provider: ToolProviderType) -> list[Tool]:
    """
    Load tools from a ToolProvider instance.

    Args:
        provider (ToolProviderType): The tool provider instance.

    Returns:
        list[Tool]: List of tools provided by the provider.
    """
    if isinstance(provider, PythonModuleToolProvider):
        return load_python_module_tools(provider)
    elif isinstance(provider, OpenAPIToolProvider):
        # TODO: Implement OpenAPI tool loading
        raise NotImplementedError("OpenAPI tool loading not yet implemented")
    else:
        raise ValueError(f"Unsupported tool provider type: {type(provider)}")
