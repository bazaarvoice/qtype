from __future__ import annotations

from typing import Any

from qtype.dsl.domain_types import ChatMessage


def default_chat_extract_text(message: Any) -> str:
    """
    Default extractor for ChatMessage or generic objects.
    """
    if isinstance(message, ChatMessage):
        return " ".join(
            [
                getattr(block, "content", "")
                for block in message.blocks
                if getattr(block, "content", "")
            ]
        )
    return str(message)
