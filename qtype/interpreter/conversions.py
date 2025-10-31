from __future__ import annotations

import importlib
from typing import Any

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.llms.types import AudioBlock
from llama_index.core.base.llms.types import ChatMessage as LlamaChatMessage
from llama_index.core.base.llms.types import (
    ContentBlock,
    DocumentBlock,
    ImageBlock,
    TextBlock,
    ThinkingBlock,
)
from llama_index.core.memory import Memory as LlamaMemory
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, RAGDocument
from qtype.dsl.model import Memory
from qtype.interpreter.auth.aws import aws
from qtype.interpreter.types import InterpreterError
from qtype.semantic.model import DocumentSplitter, Index, Model

from .resource_cache import cached_resource


def to_llama_document(doc: RAGDocument) -> LlamaDocument:
    """Convert a RAGDocument to a LlamaDocument."""
    from llama_index.core.schema import MediaResource

    # Prepare metadata, adding file_name and uri if available
    metadata = doc.metadata.copy() if doc.metadata else {}
    if doc.file_name:
        metadata["file_name"] = doc.file_name
    if doc.uri:
        metadata["url"] = (
            doc.uri
        )  # url is more commonly used in LlamaIndex metadata

    # Default text content
    text = ""
    if isinstance(doc.content, str):
        text = doc.content

    # Handle different content types
    if doc.type == PrimitiveTypeEnum.text:
        # Text content - store as text field
        return LlamaDocument(text=text, doc_id=doc.file_id, metadata=metadata)
    elif doc.type == PrimitiveTypeEnum.image and isinstance(
        doc.content, bytes
    ):
        # Image content - store in image_resource
        return LlamaDocument(
            text=text,  # Keep text empty or use as description
            doc_id=doc.file_id,
            metadata=metadata,
            image_resource=MediaResource(data=doc.content),
        )
    elif doc.type == PrimitiveTypeEnum.audio and isinstance(
        doc.content, bytes
    ):
        # Audio content - store in audio_resource
        return LlamaDocument(
            text=text,
            doc_id=doc.file_id,
            metadata=metadata,
            audio_resource=MediaResource(data=doc.content),
        )
    elif doc.type == PrimitiveTypeEnum.video and isinstance(
        doc.content, bytes
    ):
        # Video content - store in video_resource
        return LlamaDocument(
            text=text,
            doc_id=doc.file_id,
            metadata=metadata,
            video_resource=MediaResource(data=doc.content),
        )
    else:
        # Fallback for other types - store as text
        return LlamaDocument(
            text=str(doc.content) if doc.content else "",
            doc_id=doc.file_id,
            metadata=metadata,
        )


def from_llama_document(doc: LlamaDocument) -> RAGDocument:
    """Convert a LlamaDocument to a RAGDocument."""
    # Extract file_id from doc_id or id_
    file_id = doc.doc_id

    # Extract file_name from metadata or use file_id as fallback
    file_name = (
        doc.metadata.get("file_name", file_id) if doc.metadata else file_id
    )

    # Extract URI from metadata if available
    uri = (
        doc.metadata.get("url") or doc.metadata.get("uri")
        if doc.metadata
        else None
    )

    # Determine content type and extract content based on resource fields
    content_type = PrimitiveTypeEnum.text
    content: str | bytes = doc.text  # default to text

    # Check for media resources in priority order
    if hasattr(doc, "image_resource") and doc.image_resource is not None:
        content_type = PrimitiveTypeEnum.image
        # MediaResource has a 'data' field containing the bytes
        content = (
            doc.image_resource.data
            if hasattr(doc.image_resource, "data")
            else doc.text
        )  # type: ignore
    elif hasattr(doc, "audio_resource") and doc.audio_resource is not None:
        content_type = PrimitiveTypeEnum.audio
        content = (
            doc.audio_resource.data
            if hasattr(doc.audio_resource, "data")
            else doc.text
        )  # type: ignore
    elif hasattr(doc, "video_resource") and doc.video_resource is not None:
        content_type = PrimitiveTypeEnum.video
        content = (
            doc.video_resource.data
            if hasattr(doc.video_resource, "data")
            else doc.text
        )  # type: ignore

    return RAGDocument(
        content=content,
        file_id=file_id,
        file_name=file_name,
        uri=uri,
        metadata=doc.metadata.copy() if doc.metadata else None,
        type=content_type,
    )


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

    if model.provider == "aws-bedrock":
        from llama_index.llms.bedrock_converse import BedrockConverse

        if model.auth:
            with aws(model.auth) as session:
                session = session._session
        else:
            session = None

        brv: BaseLLM = BedrockConverse(
            botocore_session=session,
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
            api_key=getattr(model.auth, "api_key", None)
            if model.auth
            else None,
        )
    elif model.provider == "anthropic":
        from llama_index.llms.anthropic import (  # type: ignore[import-untyped]
            Anthropic,
        )

        arv: BaseLLM = Anthropic(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
            api_key=getattr(model.auth, "api_key", None)
            if model.auth
            else None,
        )
        return arv
    elif model.provider == "gcp-vertex":
        from llama_index.llms.vertex import Vertex

        vgv: BaseLLM = Vertex(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
        )

        return vgv
    else:
        raise InterpreterError(
            f"Unsupported model provider: {model.provider}."
        )


@cached_resource
def to_vector_store(index: Index) -> BasePydanticVectorStore:
    """Convert a qtype Index to a LlamaIndex vector store."""
    full_module_path = "llama_index.core.vector_stores" + index.args.get(
        "module", "SimpleVectorStore"
    )
    class_name = full_module_path.split(".")[-1]
    # Dynamically import the reader module
    try:
        reader_module = importlib.import_module(full_module_path)
        reader_class = getattr(reader_module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Failed to import reader class '{class_name}' from '{full_module_path}': {e}"
        ) from e

    args = index.args.copy()
    if "module" in args:
        del args["module"]

    index = reader_class(**args)

    return index


@cached_resource
def to_embedding_model(model: Model) -> BaseEmbedding:
    """Convert a qtype Model to a LlamaIndex embedding model."""

    if model.provider in {"bedrock", "aws", "aws-bedrock"}:
        from llama_index.embeddings.bedrock import (  # type: ignore[import-untyped]
            BedrockEmbedding,
        )

        bedrock_embedding: BaseEmbedding = BedrockEmbedding(
            model_name=model.model_id if model.model_id else model.id
        )
        return bedrock_embedding
    elif model.provider == "openai":
        from llama_index.embeddings.openai import (  # type: ignore[import-untyped]
            OpenAIEmbedding,
        )

        openai_embedding: BaseEmbedding = OpenAIEmbedding(
            model_name=model.model_id if model.model_id else model.id
        )
        return openai_embedding
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
        elif content.type == PrimitiveTypeEnum.bytes:
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
    blocks: list[ChatContent] = []
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
        elif isinstance(block, ThinkingBlock):
            blocks.append(
                ChatContent(
                    type=PrimitiveTypeEnum.thinking,
                    content=block.content,
                )
            )
        else:
            raise InterpreterError(
                f"Unsupported content block type: {type(block)}"
            )

    return ChatMessage(role=message.role, blocks=blocks)


def to_text_splitter(splitter: DocumentSplitter) -> Any:
    """Convert a DocumentSplitter to a LlamaIndex text splitter.

    Args:
        splitter: The DocumentSplitter configuration.

    Returns:
        An instance of the appropriate LlamaIndex text splitter class.

    Raises:
        InterpreterError: If the splitter class cannot be found or instantiated.
    """
    from llama_index.core.node_parser import SentenceSplitter

    # Map common splitter names to their classes
    splitter_classes = {
        "SentenceSplitter": SentenceSplitter,
    }

    # Get the splitter class
    splitter_class = splitter_classes.get(splitter.splitter_name)

    if splitter_class is None:
        raise InterpreterError(
            f"Unsupported text splitter: {splitter.splitter_name}. "
            f"Supported splitters: {', '.join(splitter_classes.keys())}"
        )

    # Prepare arguments for the splitter
    splitter_args = {
        "chunk_size": splitter.chunk_size,
        "chunk_overlap": splitter.chunk_overlap,
        **splitter.args,
    }

    # Instantiate and return the splitter
    try:
        return splitter_class(**splitter_args)
    except Exception as e:
        raise InterpreterError(
            f"Failed to instantiate {splitter.splitter_name}: {e}"
        ) from e
