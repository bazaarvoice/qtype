import base64

import requests

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent


def file_to_content(url: str) -> ChatContent:
    """
    Convert a file URL to a ChatContent block.

    Args:
        url: The URL of the file.

    Returns:
        A ChatContent block with type 'file' and the file URL as content.
    """
    import magic

    # Get the bytes from the url.
    if url.startswith("data:"):
        # strip the `data:` prefix and decode the base64 content
        b64content = url[len("data:") :].split(",", 1)[1]
        content = base64.b64decode(b64content)
    else:
        content = requests.get(url).content

    # Determine the mime type using python-magic
    media_type = magic.from_buffer(content, mime=True)

    if media_type.startswith("image/"):
        return ChatContent(
            type=PrimitiveTypeEnum.image, content=content, mime_type=media_type
        )
    elif media_type.startswith("video/"):
        return ChatContent(
            type=PrimitiveTypeEnum.video, content=content, mime_type=media_type
        )
    elif media_type.startswith("audio/"):
        return ChatContent(
            type=PrimitiveTypeEnum.audio, content=content, mime_type=media_type
        )
    elif media_type.startswith("text/"):
        return ChatContent(
            type=PrimitiveTypeEnum.text,
            content=content.decode("utf-8"),
            mime_type=media_type,
        )
    elif media_type.startswith("document/"):
        return ChatContent(
            type=PrimitiveTypeEnum.file, content=content, mime_type=media_type
        )
    else:
        return ChatContent(
            type=PrimitiveTypeEnum.bytes, content=content, mime_type=media_type
        )
