from qtype.interpreter.executors.aggregate_executor import AggregateExecutor
from qtype.interpreter.executors.decoder_executor import DecoderExecutor
from qtype.interpreter.executors.doc_to_text_executor import (
    DocToTextConverterExecutor,
)
from qtype.interpreter.executors.document_embedder_executor import (
    DocumentEmbedderExecutor,
)
from qtype.interpreter.executors.document_source_executor import (
    DocumentSourceExecutor,
)
from qtype.interpreter.executors.document_splitter_executor import (
    DocumentSplitterExecutor,
)
from qtype.interpreter.executors.file_source_executor import FileSourceExecutor
from qtype.interpreter.executors.file_writer_executor import FileWriterExecutor
from qtype.interpreter.executors.invoke_embedding_executor import (
    InvokeEmbeddingExecutor,
)
from qtype.interpreter.executors.invoke_tool_executor import InvokeToolExecutor
from qtype.interpreter.executors.llm_inference_executor import (
    LLMInferenceExecutor,
)
from qtype.interpreter.executors.prompt_template_executor import (
    PromptTemplateExecutor,
)
from qtype.interpreter.executors.sql_source_executor import SQLSourceExecutor
from qtype.semantic.model import (
    Aggregate,
    Decoder,
    DocToTextConverter,
    DocumentEmbedder,
    DocumentSource,
    DocumentSplitter,
    FileSource,
    FileWriter,
    InvokeEmbedding,
    InvokeTool,
    LLMInference,
    PromptTemplate,
    SQLSource,
    Step,
)

from .batch_step_executor import StepExecutor

# ... import other executors

EXECUTOR_REGISTRY = {
    LLMInference: LLMInferenceExecutor,
    FileWriter: FileWriterExecutor,
    FileSource: FileSourceExecutor,
    SQLSource: SQLSourceExecutor,
    Decoder: DecoderExecutor,
    DocToTextConverter: DocToTextConverterExecutor,
    DocumentEmbedder: DocumentEmbedderExecutor,
    DocumentSource: DocumentSourceExecutor,
    DocumentSplitter: DocumentSplitterExecutor,
    InvokeEmbedding: InvokeEmbeddingExecutor,
    InvokeTool: InvokeToolExecutor,
    Aggregate: AggregateExecutor,
    PromptTemplate: PromptTemplateExecutor,
    # ... map all other step model classes to their executor class
}


def create_executor(step: Step, **dependencies) -> StepExecutor:
    """Factory to create the appropriate executor for a given step."""
    executor_class = EXECUTOR_REGISTRY.get(type(step))
    if not executor_class:
        raise ValueError(
            f"No executor found for step type: {type(step).__name__}"
        )

    # This assumes the constructor takes the step and then dependencies
    return executor_class(step, **dependencies)
