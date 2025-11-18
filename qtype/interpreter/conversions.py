from __future__ import annotations

import importlib
import uuid
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
from opensearchpy import AWSV4SignerAuth, OpenSearch

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, RAGDocument
from qtype.dsl.model import Memory
from qtype.interpreter.auth.aws import aws
from qtype.interpreter.auth.generic import auth
from qtype.interpreter.base.secrets import SecretManagerBase
from qtype.interpreter.types import InterpreterError
from qtype.semantic.model import (
    APIKeyAuthProvider,
    DocumentIndex,
    DocumentSplitter,
    Model,
    VectorIndex,
)

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
        metadata=doc.metadata.copy() if doc.metadata else {},
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
def to_llm(
    model: Model,
    system_prompt: str | None,
    secret_manager: SecretManagerBase,
) -> BaseLLM:
    """
    Convert a qtype Model to a LlamaIndex Model.

    Args:
        model: The semantic model configuration
        system_prompt: Optional system prompt for the model
        secret_manager: Optional secret manager for resolving SecretReferences

    Returns:
        A LlamaIndex LLM instance
    """

    if model.provider == "aws-bedrock":
        from llama_index.llms.bedrock_converse import BedrockConverse

        from qtype.semantic.model import AWSAuthProvider

        if model.auth:
            # Type hint for mypy - we know it's AWSAuthProvider for aws-bedrock
            assert isinstance(model.auth, AWSAuthProvider)
            with aws(model.auth, secret_manager) as session:
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

        from qtype.interpreter.auth.generic import auth
        from qtype.semantic.model import APIKeyAuthProvider

        api_key: str | None = None
        if model.auth:
            with auth(model.auth, secret_manager) as provider:
                if not isinstance(provider, APIKeyAuthProvider):
                    raise InterpreterError(
                        f"OpenAI provider requires APIKeyAuthProvider, "
                        f"got {type(provider).__name__}"
                    )
                # api_key is guaranteed to be str after auth() resolves it
                api_key = provider.api_key  # type: ignore[assignment]

        return OpenAI(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
            api_key=api_key,
        )
    elif model.provider == "anthropic":
        from llama_index.llms.anthropic import (  # type: ignore[import-untyped]
            Anthropic,
        )

        from qtype.interpreter.auth.generic import auth
        from qtype.semantic.model import APIKeyAuthProvider

        api_key: str | None = None
        if model.auth:
            with auth(model.auth, secret_manager) as provider:
                if not isinstance(provider, APIKeyAuthProvider):
                    raise InterpreterError(
                        f"Anthropic provider requires APIKeyAuthProvider, "
                        f"got {type(provider).__name__}"
                    )
                # api_key is guaranteed to be str after auth() resolves it
                api_key = provider.api_key  # type: ignore[assignment]

        arv: BaseLLM = Anthropic(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
            api_key=api_key,
        )
        return arv
    elif model.provider == "gcp-vertex":
        from llama_index.llms.vertex import Vertex

        project_name = getattr(
            getattr(model, "auth", None), "profile_name", None
        )

        vgv: BaseLLM = Vertex(
            model=model.model_id if model.model_id else model.id,
            project=project_name,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
        )

        return vgv
    else:
        raise InterpreterError(
            f"Unsupported model provider: {model.provider}."
        )


@cached_resource
def to_vector_store(
    index: VectorIndex, secret_manager: SecretManagerBase
) -> BasePydanticVectorStore:
    """Convert a qtype Index to a LlamaIndex vector store."""
    module_path = ".".join(index.module.split(".")[:-1])
    class_name = index.module.split(".")[-1]
    # Dynamically import the reader module
    try:
        reader_module = importlib.import_module(module_path)
        reader_class = getattr(reader_module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Failed to import reader class '{class_name}' from '{module_path}': {e}"
        ) from e

    # Resolve any SecretReferences in args
    context = f"index '{index.id}'"
    resolved_args = secret_manager.resolve_secrets_in_dict(index.args, context)
    index_instance = reader_class(**resolved_args)

    return index_instance


@cached_resource
def to_embedding_model(model: Model) -> BaseEmbedding:
    """Convert a qtype Model to a LlamaIndex embedding model."""

    if model.provider == "aws-bedrock":
        from llama_index.embeddings.bedrock import (  # type: ignore[import-untyped]
            BedrockEmbedding,
        )

        bedrock_embedding: BaseEmbedding = BedrockEmbedding(
            model_name=model.model_id if model.model_id else model.id,
            max_retries=100,
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


@cached_resource
def to_opensearch_client(
    index: DocumentIndex, secret_manager: SecretManagerBase
) -> OpenSearch:
    """
    Convert a DocumentIndex to an OpenSearch/Elasticsearch client.

    Args:
        index: DocumentIndex configuration with endpoint, auth, etc.

    Returns:
        OpenSearch client instance configured with authentication

    Raises:
        InterpreterError: If authentication fails or configuration is invalid
    """
    client_kwargs: dict[str, Any] = {
        "hosts": [index.endpoint],
        **index.args,
    }

    # Handle authentication if provided
    if index.auth:
        if isinstance(index.auth, APIKeyAuthProvider):
            # Use API key authentication
            client_kwargs["api_key"] = index.auth.api_key
        elif hasattr(index.auth, "type") and index.auth.type == "aws":
            # Use AWS authentication with boto3 session
            # Get AWS credentials from auth provider using context manager
            with auth(index.auth, secret_manager) as auth_session:
                # Type checker doesn't know this is a boto3.Session
                # but runtime validation ensures it for AWS auth
                credentials = auth_session.get_credentials()  # type: ignore
                if credentials is None:
                    raise InterpreterError(
                        f"Failed to obtain AWS credentials for DocumentIndex '{index.id}'"
                    )

                # Use opensearch-py's built-in AWS auth
                aws_auth = AWSV4SignerAuth(
                    credentials,
                    auth_session.region_name or "us-east-1",  # type: ignore
                )

                client_kwargs["http_auth"] = aws_auth
                client_kwargs["use_ssl"] = True
                client_kwargs["verify_certs"] = True
        else:
            raise InterpreterError(
                f"Unsupported authentication type for DocumentIndex: {type(index.auth)}"
            )

    return OpenSearch(**client_kwargs)


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


def variable_to_chat_message(
    value: Any, variable: Any, default_role: str = "user"
) -> ChatMessage:
    """Convert any variable value to a ChatMessage based on the variable's type.

    Args:
        value: The value to convert (can be any primitive type or ChatMessage)
        variable: The Variable definition with type information
        default_role: The default message role to use (default: "user")

    Returns:
        ChatMessage with appropriate content blocks

    Raises:
        InterpreterError: If the value type cannot be converted
    """
    # If already a ChatMessage, return as-is
    if isinstance(value, ChatMessage):
        return value

    # Convert based on the variable's declared type
    var_type = variable.type
    # Handle primitive types based on variable declaration
    if isinstance(var_type, PrimitiveTypeEnum):
        # Numeric/boolean types get converted to text
        if var_type in (
            PrimitiveTypeEnum.int,
            PrimitiveTypeEnum.float,
            PrimitiveTypeEnum.boolean,
        ):
            content = ChatContent(
                type=PrimitiveTypeEnum.text, content=str(value)
            )
        # All other primitive types pass through as-is
        else:
            content = ChatContent(type=var_type, content=value)
    elif isinstance(var_type, str) and (
        var_type.startswith("list[") or var_type.startswith("dict[")
    ):
        # Handle list and dict types - convert to JSON string
        import json

        content = ChatContent(
            type=PrimitiveTypeEnum.text, content=json.dumps(value)
        )
    else:
        # Unsupported type - raise an error
        raise InterpreterError(
            f"Cannot convert variable '{variable.id}' of unsupported type "
            f"'{var_type}' to ChatMessage"
        )

    return ChatMessage(role=default_role, blocks=[content])  # type: ignore


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
            continue
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

    module_path = "llama_index.core.node_parser"
    class_name = splitter.splitter_name
    try:
        reader_module = importlib.import_module(module_path)
        splitter_class = getattr(reader_module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Failed to import reader class '{class_name}' from '{module_path}': {e}"
        ) from e
    from llama_index.core.schema import BaseNode

    # TODO: let the user specify a custom ID namespace
    namespace = uuid.UUID("12345678-1234-5678-1234-567812345678")

    def id_func(i: int, doc: BaseNode) -> str:
        u = uuid.uuid5(namespace, f"{doc.node_id}_{i}")
        return str(u)

    # Prepare arguments for the splitter
    splitter_args = {
        "chunk_size": splitter.chunk_size,
        "chunk_overlap": splitter.chunk_overlap,
        "id_func": id_func,
        **splitter.args,
    }

    # Instantiate and return the splitter
    try:
        return splitter_class(**splitter_args)
    except Exception as e:
        raise InterpreterError(
            f"Failed to instantiate {splitter.splitter_name}: {e}"
        ) from e


def to_llama_vector_store_and_retriever(
    index: VectorIndex, secret_manager: SecretManagerBase
) -> tuple[BasePydanticVectorStore, Any]:
    """Create a LlamaIndex vector store and retriever from a VectorIndex.

    Args:
        index: VectorIndex configuration

    Returns:
        Tuple of (vector_store, retriever)
    """
    from llama_index.core import VectorStoreIndex

    # Get the vector store using existing function
    vector_store = to_vector_store(index, secret_manager)

    # Get the embedding model
    embedding_model = to_embedding_model(index.embedding_model)

    # Create a VectorStoreIndex with the vector store and embedding model
    vector_index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )

    # Create retriever with optional top_k configuration
    retriever = vector_index.as_retriever()

    return vector_store, retriever


def from_node_with_score(node_with_score) -> Any:
    """Convert a LlamaIndex NodeWithScore to a RAGSearchResult.

    Args:
        node_with_score: LlamaIndex NodeWithScore object

    Returns:
        RAGSearchResult with chunk and score
    """
    from qtype.dsl.domain_types import RAGChunk, RAGSearchResult

    node = node_with_score.node

    # Extract vector if available
    vector = None
    if hasattr(node, "embedding") and node.embedding is not None:
        vector = node.embedding

    # Create RAGChunk from node
    chunk = RAGChunk(
        content=node.text or "",
        chunk_id=node.node_id,
        document_id=node.metadata.get("document_id", node.node_id),
        vector=vector,
        metadata=node.metadata or {},
    )

    # Wrap in RAGSearchResult with score
    return RAGSearchResult(chunk=chunk, score=node_with_score.score or 0.0)
