### ChatContent

`ChatContent` represents a single content block within a chat message. Each message can contain multiple blocks of different types.

#### Fields

- **type** (`PrimitiveTypeEnum`): The type of content. Supported types include:
  - `text` - Plain text content
  - `image` - Image data (bytes or base64)
  - `audio` - Audio data
  - `video` - Video data
  - `file` - File attachment
  - `bytes` - Raw byte data
  - `citation_url` - URL citation/reference
  - `citation_document` - Document citation/reference
- **content** (`Any`): The actual content, which varies by type:
  - For `text`: string value
  - For media types (`image`, `audio`, `video`): bytes or encoded data
  - For `citation_url`: dictionary with `{"source_id": str, "url": str, "title": str | None}`
  - For `citation_document`: dictionary with `{"source_id": str, "title": str, "filename": str | None, "media_type": str}`
- **mime_type** (`str | None`): The MIME type of the content, if known. Useful for media types.

#### Citation Types

Citation types are used to reference sources without mixing them with regular message content:

```python
# URL Citation
ChatContent(
    type=PrimitiveTypeEnum.citation_url,
    content={
        "source_id": "src-123",
        "url": "https://example.com/article",
        "title": "Example Article"
    }
)

# Document Citation
ChatContent(
    type=PrimitiveTypeEnum.citation_document,
    content={
        "source_id": "doc-456",
        "title": "Research Paper",
        "filename": "paper.pdf",
        "media_type": "application/pdf"
    }
)
```
