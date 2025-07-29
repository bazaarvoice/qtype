# Application

Defines a QType application that can include models, variables, and other components.

## Members
- **id** (`str`): Unique ID of the application.
- **description** (`str | None`): Optional description of the application.
- **memories** (`list[Memory] | None`): List of memory definitions used in this application.
- **models** (`list[ModelType] | None`): List of models used in this application.
- **types** (`list[ObjectTypeDefinition | ArrayTypeDefinition] | None`): List of custom types defined in this application.
- **variables** (`list[Variable] | None`): List of variables used in this application.
- **flows** (`list[Flow] | None`): List of flows defined in this application.
- **auths** (`list[AuthorizationProvider] | None`): List of authorization providers used for API access.
- **tools** (`list[ToolType] | None`): List of tools available in this application.
- **indexes** (`list[IndexType] | None`): List of indexes available for search operations.
- **telemetry** (`TelemetrySink | None`): Optional telemetry sink for observability.
- **references** (`list[Document] | None`): List of other q-type documents you may use. This allows modular composition and reuse of components across applications.

---
