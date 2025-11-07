import importlib
from typing import AsyncIterator

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import from_llama_document
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import DocumentSource


class DocumentSourceExecutor(StepExecutor):
    """Executor for DocumentSource steps."""

    def __init__(
        self, step: DocumentSource, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, DocumentSource):
            raise ValueError(
                (
                    "DocumentSourceExecutor can only execute "
                    "DocumentSource steps."
                )
            )
        self.step: DocumentSource = step
        # Initialize the reader class once for the executor
        self.reader_class = self._load_reader_class()

    def _load_reader_class(self) -> type:
        """Load the LlamaIndex reader class dynamically.

        Returns:
            The reader class.

        Raises:
            ImportError: If the reader class cannot be imported.
        """
        # Parse the reader module path
        # Format: 'file.SimpleDirectoryReader' -> llama_index.readers.file + SimpleDirectoryReader
        # Special case: 'file.SimpleDirectoryReader' is actually in llama_index.core
        parts = self.step.reader_module.split(".")
        module_path = ".".join(parts[:-1])
        class_name = parts[-1]

        # Dynamically import the reader module and get the class
        try:
            module = importlib.import_module(module_path)
            reader_class = getattr(module, class_name)
            return reader_class
        except (ImportError, AttributeError) as e:
            raise ImportError(
                (
                    f"Failed to import reader class '{class_name}' "
                    f"from '{module_path}': {e}"
                )
            ) from e

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the DocumentSource step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessages with loaded documents.
        """
        output_id = self.step.outputs[0].id

        try:
            # Resolve any SecretReferences in step args
            context = f"step '{self.step.id}'"
            resolved_args = self._secret_manager.resolve_secrets_in_dict(
                self.step.args, context
            )

            # Combine resolved step args with message variables as runtime args
            runtime_args = {
                key: message.variables.get(key)
                for key in message.variables.keys()
            }
            combined_args = {**resolved_args, **runtime_args}

            # Instantiate the reader with combined arguments
            loader = self.reader_class(**combined_args)

            # Load documents using the loader
            if not hasattr(loader, "load_data"):
                raise AttributeError(
                    (
                        f"Reader class '{self.reader_class.__name__}' "
                        "does not have a 'load_data' method"
                    )
                )
            load_args = self.step.loader_args or {}

            llama_documents = loader.load_data(**load_args)

            # Convert LlamaIndex Documents to RAGDocuments
            rag_documents = [
                from_llama_document(doc) for doc in llama_documents
            ]

            # Emit feedback about total documents loaded
            await self.stream_emitter.status(
                f"Loaded {len(rag_documents)} documents"
            )

            # Yield one message per document (fan-out)
            for doc in rag_documents:
                yield message.copy_with_variables({output_id: doc})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
