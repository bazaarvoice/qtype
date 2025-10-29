### Application

Defines a complete QType application specification.
An Application is the top-level container of the entire
program in a QType YAML file. It serves as the blueprint for your
AI-powered application, containing all the models, flows, tools, data sources,
and configuration needed to run your program. Think of it as the main entry
point that ties together all components into a cohesive,
executable system.

- **id** (`str`): Unique ID of the application.
- **description** (`str | None`): Optional description of the application.
- **memories** (`list[Memory]`): List of memory definitions used in this application.
- **models** (`list[ModelType]`): List of models used in this application.
- **types** (`list[CustomType]`): List of custom types defined in this application.
- **flows** (`list[Flow]`): List of flows defined in this application.
- **auths** (`list[AuthProviderType]`): List of authorization providers used for API access.
- **tools** (`list[ToolType]`): List of tools available in this application.
- **indexes** (`list[IndexType]`): List of indexes available for search operations.
- **telemetry** (`TelemetrySink | None`): Optional telemetry sink for observability.
- **references** (`list[Document]`): List of other q-type documents you may use. This allows modular composition and reuse of components across applications.
