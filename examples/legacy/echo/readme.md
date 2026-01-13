# Echo Examples

These examples are intended to be for testing purposes or early stage development. Output will be a replicate of the input.

**Primitive types**
```
class PrimitiveTypeEnum(str, Enum):
    """Represents the type of data a user or system input can accept within the DSL."""

    audio = "audio"
    boolean = "boolean"
    bytes = "bytes"
    citation_document = "citation_document"
    citation_url = "citation_url"
    date = "date"
    datetime = "datetime"
    int = "int"
    file = "file"
    float = "float"
    image = "image"
    text = "text"
    time = "time"
    video = "video"
    thinking = "thinking"
```
To test out a primitive type:

- Duplicate `examples/echo/video.qtype.yaml`
- Replace all mentions of video with the primitive type you wish to test