from qtype.interpreter.executors.agent_executor import AgentExecutor
from qtype.interpreter.executors.aggregate_executor import AggregateExecutor
from qtype.interpreter.executors.decoder_executor import DecoderExecutor
from qtype.interpreter.executors.doc_to_text_executor import (
    DocToTextConverterExecutor,
)
from qtype.interpreter.executors.document_embedder_executor import (
    DocumentEmbedderExecutor,
)
from qtype.interpreter.executors.document_search_executor import (
    DocumentSearchExecutor,
)
from qtype.interpreter.executors.document_source_executor import (
    DocumentSourceExecutor,
)
from qtype.interpreter.executors.document_splitter_executor import (
    DocumentSplitterExecutor,
)
from qtype.interpreter.executors.echo_executor import EchoExecutor
from qtype.interpreter.executors.field_extractor_executor import (
    FieldExtractorExecutor,
)
from qtype.interpreter.executors.file_source_executor import FileSourceExecutor
from qtype.interpreter.executors.file_writer_executor import FileWriterExecutor
from qtype.interpreter.executors.index_upsert_executor import (
    IndexUpsertExecutor,
)
from qtype.interpreter.executors.invoke_embedding_executor import (
    InvokeEmbeddingExecutor,
)
from qtype.interpreter.executors.invoke_flow_executor import InvokeFlowExecutor
from qtype.interpreter.executors.invoke_tool_executor import InvokeToolExecutor
from qtype.interpreter.executors.llm_inference_executor import (
    LLMInferenceExecutor,
)
from qtype.interpreter.executors.prompt_template_executor import (
    PromptTemplateExecutor,
)
from qtype.interpreter.executors.sql_source_executor import SQLSourceExecutor
from qtype.interpreter.executors.vector_search_executor import (
    VectorSearchExecutor,
)
from qtype.semantic.model import (
    Agent,
    Aggregate,
    Decoder,
    DocToTextConverter,
    DocumentEmbedder,
    DocumentSearch,
    DocumentSource,
    DocumentSplitter,
    Echo,
    FieldExtractor,
    FileSource,
    FileWriter,
    IndexUpsert,
    InvokeEmbedding,
    InvokeFlow,
    InvokeTool,
    LLMInference,
    PromptTemplate,
    SQLSource,
    Step,
    VectorSearch,
)

from .batch_step_executor import StepExecutor
from .executor_context import ExecutorContext

# ... import other executors

EXECUTOR_REGISTRY = {
    Agent: AgentExecutor,
    Aggregate: AggregateExecutor,
    Decoder: DecoderExecutor,
    DocToTextConverter: DocToTextConverterExecutor,
    DocumentEmbedder: DocumentEmbedderExecutor,
    DocumentSearch: DocumentSearchExecutor,
    DocumentSource: DocumentSourceExecutor,
    DocumentSplitter: DocumentSplitterExecutor,
    Echo: EchoExecutor,
    FieldExtractor: FieldExtractorExecutor,
    FileSource: FileSourceExecutor,
    FileWriter: FileWriterExecutor,
    IndexUpsert: IndexUpsertExecutor,
    InvokeEmbedding: InvokeEmbeddingExecutor,
    InvokeFlow: InvokeFlowExecutor,
    InvokeTool: InvokeToolExecutor,
    LLMInference: LLMInferenceExecutor,
    PromptTemplate: PromptTemplateExecutor,
    SQLSource: SQLSourceExecutor,
    VectorSearch: VectorSearchExecutor,
}


def create_executor(
    step: Step, context: ExecutorContext, **dependencies
) -> StepExecutor:
    """
    Factory to create the appropriate executor for a given step.

    Args:
        step: The step to create an executor for
        context: ExecutorContext containing cross-cutting concerns
        **dependencies: Executor-specific dependencies

    Returns:
        StepExecutor: Configured executor instance
    """
    executor_class = EXECUTOR_REGISTRY.get(type(step))
    if not executor_class:
        raise ValueError(
            f"No executor found for step type: {type(step).__name__}"
        )

    # This assumes the constructor takes the step, context, then dependencies
    return executor_class(step, context, **dependencies)
