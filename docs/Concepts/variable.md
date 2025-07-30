# Variable

Every input and output to all [Step](step.md)s, including [Flow](flow.md)s, must be defined as a variable.

Each variable must have a unique id. This is used to reference it from across your application. If conflicting, you'll recieve a validation error.

The variable `type` can be either a primitive or a type defined for specific domains.

--8<-- "components/Variable.md"

--8<-- "components/PrimitiveTypeEnum.md"

## Domain Specific Types

Domain specific types are included for common use cases (chat bots, RAG, etc)


--8<-- "components/ChatMessage.md"
--8<-- "components/ChatContent.md"
--8<-- "components/Embedding.md"
