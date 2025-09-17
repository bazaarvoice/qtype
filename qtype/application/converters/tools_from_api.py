import logging
from pathlib import Path
from typing import Optional

from openapi_parser import parse
from openapi_parser.enumeration import (
    AuthenticationScheme,
    DataType,
    SecurityType,
)
from openapi_parser.specification import Array, Object, Operation
from openapi_parser.specification import Path as OAPIPath
from openapi_parser.specification import (
    RequestBody,
    Response,
    Schema,
    Security,
)

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.model import (
    APIKeyAuthProvider,
    APITool,
    AuthorizationProvider,
    AuthProviderType,
    CustomType,
    OAuth2AuthProvider,
    Variable,
    VariableType,
)


def _schema_to_qtype_properties(
    schema: Schema,
    existing_custom_types: dict[str, CustomType],
    schema_name_map: dict[int, str] | None = None,
) -> dict[str, str]:
    """Convert OpenAPI Schema properties to QType CustomType properties."""
    properties = {}

    # Check if schema is an Object type with properties
    if isinstance(schema, Object) and schema.properties:
        # Get the list of required properties for this object
        required_props = schema.required or []

        for prop in schema.properties:
            prop_type = _schema_to_qtype_type(
                prop.schema, existing_custom_types, schema_name_map
            )
            # Convert to string representation for storage in properties dict
            prop_type_str = _type_to_string(prop_type)

            # Add '?' suffix for optional properties (not in required list)
            if prop.name not in required_props:
                prop_type_str += "?"

            properties[prop.name] = prop_type_str
    else:
        # For non-object schemas, create a default property
        default_type = _schema_to_qtype_type(
            schema, existing_custom_types, schema_name_map
        )
        default_type_str = _type_to_string(default_type)
        properties["value"] = default_type_str

    return properties


def _type_to_string(qtype: PrimitiveTypeEnum | CustomType | str) -> str:
    """Convert a QType to its string representation."""
    if isinstance(qtype, PrimitiveTypeEnum):
        return qtype.value
    elif isinstance(qtype, CustomType):
        return qtype.id
    else:
        return qtype  # Already a string


def _create_custom_type_from_schema(
    schema: Schema,
    existing_custom_types: dict[str, CustomType],
    schema_name_map: dict[int, str],
) -> CustomType:
    """Create a CustomType from an Object schema."""
    # Generate a unique ID for this schema-based type
    type_id = None

    schema_hash = hash(str(schema))
    if schema_hash in schema_name_map:
        type_id = schema_name_map[schema_hash]
    else:
        # make a type id manually
        if schema.title:
            # Use title if available, make it lowercase, alphanumeric, snake_case
            base_id = schema.title.lower().replace(" ", "_").replace("-", "_")
            # Remove non-alphanumeric characters except underscores
            type_id = "schema_" + "".join(
                c for c in base_id if c.isalnum() or c == "_"
            )
        else:
            # Fallback to hash if no title
            type_id = f"schema_{hash(str(schema))}"

    # Check if we already have this type
    if type_id in existing_custom_types:
        return existing_custom_types[type_id]

    # Create properties from the schema
    properties = _schema_to_qtype_properties(
        schema, existing_custom_types, schema_name_map
    )

    # Create the custom type
    custom_type = CustomType(
        id=type_id,
        description=schema.description
        or schema.title
        or "Generated from OpenAPI schema",
        properties=properties,
    )

    # Store it in the registry to prevent infinite recursion
    existing_custom_types[type_id] = custom_type

    return custom_type


def _schema_to_qtype_type(
    schema: Schema,
    existing_custom_types: dict[str, CustomType],
    schema_name_map: dict[int, str],
) -> PrimitiveTypeEnum | CustomType | str:
    """Recursively convert OpenAPI Schema to QType, handling nested types."""
    match schema.type:
        case DataType.STRING:
            return PrimitiveTypeEnum.text
        case DataType.INTEGER:
            return PrimitiveTypeEnum.int
        case DataType.NUMBER:
            return PrimitiveTypeEnum.float
        case DataType.BOOLEAN:
            return PrimitiveTypeEnum.boolean
        case DataType.ARRAY:
            if isinstance(schema, Array) and schema.items:
                item_type = _schema_to_qtype_type(
                    schema.items, existing_custom_types, schema_name_map
                )
                item_type_str = _type_to_string(item_type)
                return f"list[{item_type_str}]"
            return "list[text]"  # Default to list of text when no item type is specified
        case DataType.OBJECT:
            # For object types, create a custom type
            return _create_custom_type_from_schema(
                schema, existing_custom_types, schema_name_map
            )
        case DataType.NULL:
            return PrimitiveTypeEnum.text  # Default to text for null types
        case _:
            return PrimitiveTypeEnum.text  # Default fallback


def to_variable_type(
    oas: Response | RequestBody,
    existing_custom_types: dict[str, CustomType],
    schema_name_map: dict[int, str] | None = None,
) -> VariableType | CustomType:
    """
    Convert an OpenAPI Response or RequestBody to a VariableType or CustomType.
    If it already exists in existing_custom_types, return that instance.
    """
    # Check if we have content to analyze
    if not hasattr(oas, "content") or not oas.content:
        # No content available, default to text
        return PrimitiveTypeEnum.text

    # Get the first content schema
    schema = None
    for content in oas.content:
        if hasattr(content, "schema") and content.schema:
            schema = content.schema
            break

    if schema is None:
        return PrimitiveTypeEnum.text

    # Use the recursive schema conversion function
    result = _schema_to_qtype_type(
        schema, existing_custom_types, schema_name_map
    )

    # If it's a string (like "list[text]"), we need to return it as-is for now
    # The semantic layer will handle string-based type references
    if isinstance(result, str):
        # For now, return as text since we can't directly represent complex string types
        # in VariableType union. The semantic resolver will handle this.
        return PrimitiveTypeEnum.text

    return result


def to_api_tool(
    server_url: str,
    auth: Optional[AuthorizationProvider],
    path: OAPIPath,
    operation: Operation,
    existing_custom_types: dict[str, CustomType],
    schema_name_map: dict[int, str],
) -> APITool:
    """Convert an OpenAPI Path and Operation to a Tool."""
    endpoint = server_url.rstrip("/") + path.url

    # Generate a unique ID for this tool
    tool_id = (
        operation.operation_id
        or f"{operation.method.value}_{path.url.replace('/', '_').replace('{', '').replace('}', '')}"
    )

    # Use operation summary as name, fallback to operation_id or generated name
    tool_name = (
        operation.summary
        or operation.operation_id
        or f"{operation.method.value.upper()} {path.url}"
    )

    # Use operation description, fallback to summary or generated description
    tool_description = (
        operation.description
        or operation.summary
        or f"API call to {operation.method.value.upper()} {path.url}"
    )

    # Process inputs from request body and parameters
    inputs = []
    if operation.request_body and operation.request_body.content:
        # Create input variable from request body
        input_type = to_variable_type(
            operation.request_body, existing_custom_types, schema_name_map
        )
        # Convert CustomType to string ID for Variable
        if isinstance(input_type, CustomType):
            input_type_value = input_type.id
        else:
            input_type_value = input_type
        input_var = Variable(
            id=tool_id + "_request_body", type=input_type_value
        )
        inputs.append(input_var)

    # Add path and query parameters as inputs
    for param in operation.parameters:
        if param.schema:
            param_type = _schema_to_qtype_type(
                param.schema, existing_custom_types, schema_name_map
            )
            # Convert to appropriate type for Variable
            if isinstance(param_type, CustomType):
                param_type_value = param_type.id
            elif isinstance(param_type, str):
                param_type_value = param_type
            else:
                param_type_value = param_type
            param_var = Variable(id=param.name, type=param_type_value)
            inputs.append(param_var)

    # Process outputs from responses
    outputs = []
    # Find the success response (200-299 status codes)
    success_response = None
    for response in operation.responses:
        if response.code and 200 <= response.code < 300:
            success_response = response
            break

    # If no explicit success response, try to find the default response
    if not success_response:
        for response in operation.responses:
            if response.is_default:
                success_response = response
                break

    # If we found a success response, create output variable
    if success_response and success_response.content:
        output_type = to_variable_type(
            success_response, existing_custom_types, schema_name_map
        )
        # Convert CustomType to string ID for Variable
        if isinstance(output_type, CustomType):
            output_type_value = output_type.id
        else:
            output_type_value = output_type
        output_var = Variable(id=tool_id + "response", type=output_type_value)
        outputs.append(output_var)

    return APITool(
        id=tool_id,
        name=tool_name,
        description=tool_description,
        endpoint=endpoint,
        method=operation.method.value.upper(),
        auth=auth.id if auth else None,  # Use auth ID string instead of object
        inputs=inputs if inputs else None,
        outputs=outputs if outputs else None,
    )


def to_authorization_provider(
    api_name: str, scheme_name: str, security: Security
) -> AuthProviderType:
    if security.scheme is None:
        raise ValueError("Security scheme is missing")

    match security.type:
        case SecurityType.API_KEY:
            return APIKeyAuthProvider(
                id=f"{api_name}_{scheme_name}_{security.name or 'api_key'}",
                api_key="your_api_key_here",  # User will need to configure
                host=None,  # Will be set from base URL if available
            )
        case SecurityType.HTTP:
            if security.scheme == AuthenticationScheme.BEARER:
                return APIKeyAuthProvider(
                    id=f"{api_name}_{scheme_name}_{security.bearer_format or 'token'}",
                    api_key="your_bearer_token_here",  # User will need to configure
                    host=None,
                )
            else:
                raise ValueError(
                    f"HTTP authentication scheme '{security.scheme}' is not supported"
                )
        case SecurityType.OAUTH2:
            return OAuth2AuthProvider(
                id=f"{api_name}_{scheme_name}_{hash(str(security.flows))}",
                client_id="your_client_id",  # User will need to configure
                client_secret="your_client_secret",  # User will need to configure
                token_url=next(
                    (
                        flow.token_url
                        for flow in security.flows.values()
                        if flow.token_url
                    ),
                    "https://example.com/oauth/token",  # Default fallback
                ),
                scopes=list(
                    {
                        scope
                        for flow in security.flows.values()
                        for scope in flow.scopes.keys()
                    }
                )
                if any(flow.scopes for flow in security.flows.values())
                else None,
            )
        case _:
            raise ValueError(
                f"Security type '{security.type}' is not supported"
            )


def tools_from_api(
    openapi_spec: str,
) -> tuple[str, list[AuthProviderType], list[APITool], list[CustomType]]:
    """
    Creates tools from an OpenAPI specification.

    Args:
        module_path: The OpenAPI specification path or URL.

    Returns:
        Application: An Application instance containing tools and authorization
        examples for using the api.

    Raises:
        ImportError: If the OpenAPI spec cannot be loaded.
        ValueError: If no valid endpoints are found in the spec.
    """

    # load the spec using
    specification = parse(openapi_spec)
    api_name = (
        specification.info.title.lower().replace(" ", "-")
        if specification.info and specification.info.title
        else Path(openapi_spec).stem
    )
    # remove any non alphanumeric characters except hyphens and underscores
    api_name = "".join(c for c in api_name if c.isalnum() or c in ("-", "_"))

    # If security is specified, create an authorization provider.
    authorization_providers = [
        to_authorization_provider(api_name, name.lower(), sec)
        for name, sec in specification.security_schemas.items()
    ]

    if len(specification.servers) > 0:
        server_url = specification.servers[0].url
    else:
        logging.warning(
            "No servers defined in the OpenAPI specification. Using http://localhost as default."
        )
        server_url = "http://localhost"

    # Create tools from the parsed specification
    existing_custom_types: dict[str, CustomType] = {}
    tools = []

    # Create a mapping from schema hash to their names in the OpenAPI spec
    # Note: We can't monkey-patch here since the openapi_parser duplicates instances in memory
    # if they are $ref'd in the content
    schema_name_map: dict[int, str] = {
        hash(str(schema)): name.replace(" ", "-").replace("_", "-")
        for name, schema in specification.schemas.items()
    }

    # Get the default auth provider if available
    default_auth = (
        authorization_providers[0] if authorization_providers else None
    )

    # Iterate through all paths and operations
    for path in specification.paths:
        for operation in path.operations:
            api_tool = to_api_tool(
                server_url=server_url,
                auth=default_auth,
                path=path,
                operation=operation,
                existing_custom_types=existing_custom_types,
                schema_name_map=schema_name_map,
            )
            tools.append(api_tool)

    if not tools:
        raise ValueError(
            "No valid endpoints found in the OpenAPI specification"
        )

    # Convert custom types to a list
    custom_types = list(existing_custom_types.values())

    return api_name, authorization_providers, tools, custom_types
