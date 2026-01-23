# Create Tools from OpenAPI Specifications

Generate QType tool definitions automatically from OpenAPI/Swagger specifications using `qtype convert api`, which parses API endpoints, parameters, and schemas to create properly typed API tools.

### Command

```bash
# Convert from a URL (or use a local file path)
qtype convert api https://petstore3.swagger.io/api/v3/openapi.json --output petstore_tools.qtype.yaml
```

This creates the `petstore_tools.qtype.yaml` qtype file you can import into your application.

### QType YAML

**Generated tool YAML** (`petstore_tools.qtype.yaml`):
```yaml
id: swagger-petstore---openapi-30
description: Tools created from API specification petstore_api.json

auths:
  - id: swagger-petstore---openapi-30_api_key_api_key
    type: api_key
    api_key: your_api_key_here

tools:
  - id: getPetById
    name: Find pet by ID.
    description: Returns a single pet.
    type: APITool
    method: GET
    endpoint: /api/v3/pet/{petId}
    auth: swagger-petstore---openapi-30_api_key_api_key
    inputs:
      - id: petId
        type: int
    outputs:
      - id: id
        type: int?
      - id: name
        type: text
      - id: status
        type: text?
    parameters: []
```

### Explanation

- **`convert api`**: CLI subcommand that converts OpenAPI specifications to tool definitions
- **OpenAPI spec**: JSON or YAML file following OpenAPI 3.0+ or Swagger 2.0 format
- **`--output`**: Target YAML file path; omit to print to stdout
- **operationId**: Becomes the tool ID (e.g., `getPetById`)
- **parameters**: Path, query, and header parameters become tool `parameters`
- **responses**: Response schema properties become tool `outputs`
- **servers**: Base URL is combined with path to create full endpoint
- **method**: HTTP method (GET, POST, PUT, DELETE, etc.)
- **securitySchemes**: Generates auth providers (API key, OAuth2, Bearer token)

### Using Generated Tools

```yaml
references:
  - !include petstore_tools.qtype.yaml

flows:
  - id: fetch_pet
    steps:
      - type: InvokeTool
        id: get_pet
        tool: getPetById
        input_bindings:
          petId: pet_id
        output_bindings:
          name: pet_name
          status: pet_status
```

See [Tutorial: Adding Tools to Your Application](../../Tutorials/04-tools-and-function-calling.md) for a detailed usage.


## See Also

- [Tutorial: Adding Tools to Your Application](../../Tutorials/04-tools-and-function-calling.md)
- [How-To: Create Tools from Python Modules](create_tools_from_python_modules.md)
- [InvokeTool Reference](../../components/InvokeTool.md)
- [APITool Reference](../../components/APITool.md)
