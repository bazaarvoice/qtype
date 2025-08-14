# Creating Custom Types

QType allows you to create custom types for variable inputs and outputs. 

Custom types must be defined the in `types` list in your [Application](../components/Application.md). They _can not_ be defined in-line in variables.

Internally, custom types are mapped to pydantic objects.

--8<-- "components/CustomType.md"

## A Simple Example

The following example illustrates the key features of custom types:

* The custom types `Arthor` and `Book` are defined. Those terms can be used as a `type` in any variable.
* All fields of the custom types should be other custom types, [primitive types](../components/PrimitiveTypeEnum.md), or [domain types](./domain-types.md)
* A `?` can be used after the type to indicate it is optional. In this case, it will be `None` if not provided.
* A `list[type]` can be used to indicate a list.
* Forward references are allowed -- `Book` references `Arthor` which is defined later



```yaml
id: valid_custom_type
types:
  - id: Book
    properties:
      title: text
      author: Author # <-- this is a forward reference
      year: int?
      tags: "list[text]"
      published: boolean
  - id: Author
    properties:
      id: int
      name: text
flows:
  - id: my_person_flow
    mode: Complete
    steps:
      - id: prompt_template
        template: >
          You are a helpful assistant. Please provide information about the following book:
          {book}
        inputs:
          - id: book
            type: Book
        outputs:
          - id: prompt_format
            type: text
```

