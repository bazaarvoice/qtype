from __future__ import annotations

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.llms.types import AudioBlock
from llama_index.core.base.llms.types import ChatMessage as LlamaChatMessage
from llama_index.core.base.llms.types import (
    ContentBlock,
    DocumentBlock,
    ImageBlock,
    TextBlock,
)
from llama_index.core.memory import Memory as LlamaMemory

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage
from qtype.dsl.model import Memory
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import Model

from .resource_cache import cached_resource


@cached_resource
def to_memory(session_id: str | None, memory: Memory) -> LlamaMemory:
    return LlamaMemory.from_defaults(
        session_id=session_id,
        token_limit=memory.token_limit,
        chat_history_token_ratio=memory.chat_history_token_ratio,
        token_flush_size=memory.token_flush_size,
    )


@cached_resource
def to_llm(model: Model, system_prompt: str | None) -> BaseLLM:
    """Convert a qtype Model to a LlamaIndex Model."""

    if model.provider in "aws-bedrock":
        # BedrockConverse requires a model_id and system_prompt
        # Inference params can be passed as additional kwargs
        from llama_index.llms.bedrock_converse import BedrockConverse

        brv: BaseLLM = BedrockConverse(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
        )
        return brv
    elif model.provider == "openai":
        from llama_index.llms.openai import OpenAI

        return OpenAI(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
            api_key=model.auth.api_key
            if model.auth and model.auth.api_key
            else None,
        )
    elif model.provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic

        arv: BaseLLM = Anthropic(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
        )
        return arv
    else:
        raise InterpreterError(
            f"Unsupported model provider: {model.provider}."
        )


@cached_resource
def to_embedding_model(model: Model) -> BaseEmbedding:
    """Convert a qtype Model to a LlamaIndex embedding model."""

    if model.provider in {"bedrock", "aws", "aws-bedrock"}:
        from llama_index.embeddings.bedrock import BedrockEmbedding

        embedding: BaseEmbedding = BedrockEmbedding(
            model_name=model.model_id if model.model_id else model.id
        )
        return embedding
    elif model.provider == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding

        embedding: BaseEmbedding = OpenAIEmbedding(
            model_name=model.model_id if model.model_id else model.id
        )
        return embedding
    else:
        raise InterpreterError(
            f"Unsupported embedding model provider: {model.provider}."
        )


def to_content_block(content: ChatContent) -> ContentBlock:
    if content.type == PrimitiveTypeEnum.text:
        if isinstance(content.content, str):
            # If content is a string, return a TextBlock
            return TextBlock(text=content.content)
        else:
            # If content is not a string, raise an error
            raise InterpreterError(
                f"Expected content to be a string, got {type(content.content)}"
            )
    elif isinstance(content.content, bytes):
        if content.type == PrimitiveTypeEnum.image:
            return ImageBlock(image=content.content)
        elif content.type == PrimitiveTypeEnum.audio:
            return AudioBlock(audio=content.content)
        elif content.type == PrimitiveTypeEnum.file:
            return DocumentBlock(data=content.content)

    raise InterpreterError(
        f"Unsupported content type: {content.type} with data of type {type(content.content)}"
    )


def to_chat_message(message: ChatMessage) -> LlamaChatMessage:
    """Convert a ChatMessage to a LlamaChatMessage."""
    blocks = [to_content_block(content) for content in message.blocks]
    return LlamaChatMessage(role=message.role, content=blocks)


def from_chat_message(message: LlamaChatMessage) -> ChatMessage:
    """Convert a LlamaChatMessage to a ChatMessage."""
    blocks = []
    for block in message.blocks:
        if isinstance(block, TextBlock):
            blocks.append(
                ChatContent(type=PrimitiveTypeEnum.text, content=block.text)
            )
        elif isinstance(block, ImageBlock):
            blocks.append(
                ChatContent(type=PrimitiveTypeEnum.image, content=block.image)
            )
        elif isinstance(block, AudioBlock):
            blocks.append(
                ChatContent(type=PrimitiveTypeEnum.audio, content=block.audio)
            )
        elif isinstance(block, DocumentBlock):
            blocks.append(
                ChatContent(type=PrimitiveTypeEnum.file, content=block.data)
            )
        else:
            raise InterpreterError(
                f"Unsupported content block type: {type(block)}"
            )

    return ChatMessage(role=message.role, blocks=blocks)  # type: ignore
