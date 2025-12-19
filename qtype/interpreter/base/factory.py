from qtype.semantic.model import (
    Agent,
    Aggregate,
    BedrockReranker,
    Collect,
    Construct,
    Decoder,
    DocToTextConverter,
    DocumentEmbedder,
    DocumentSearch,
    DocumentSource,
    DocumentSplitter,
    Echo,
    Explode,
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

# Lazy-load executor classes only when needed
# This avoids importing heavy dependencies until actually required
EXECUTOR_REGISTRY = {
    Agent: "qtype.interpreter.executors.agent_executor.AgentExecutor",
    Aggregate: "qtype.interpreter.executors.aggregate_executor.AggregateExecutor",
    BedrockReranker: "qtype.interpreter.executors.bedrock_reranker_executor.BedrockRerankerExecutor",
    Collect: "qtype.interpreter.executors.collect_executor.CollectExecutor",
    Construct: "qtype.interpreter.executors.construct_executor.ConstructExecutor",
    Decoder: "qtype.interpreter.executors.decoder_executor.DecoderExecutor",
    DocToTextConverter: "qtype.interpreter.executors.doc_to_text_executor.DocToTextConverterExecutor",
    DocumentEmbedder: "qtype.interpreter.executors.document_embedder_executor.DocumentEmbedderExecutor",
    DocumentSearch: "qtype.interpreter.executors.document_search_executor.DocumentSearchExecutor",
    DocumentSource: "qtype.interpreter.executors.document_source_executor.DocumentSourceExecutor",
    DocumentSplitter: "qtype.interpreter.executors.document_splitter_executor.DocumentSplitterExecutor",
    Echo: "qtype.interpreter.executors.echo_executor.EchoExecutor",
    Explode: "qtype.interpreter.executors.explode_executor.ExplodeExecutor",
    FieldExtractor: "qtype.interpreter.executors.field_extractor_executor.FieldExtractorExecutor",
    FileSource: "qtype.interpreter.executors.file_source_executor.FileSourceExecutor",
    FileWriter: "qtype.interpreter.executors.file_writer_executor.FileWriterExecutor",
    IndexUpsert: "qtype.interpreter.executors.index_upsert_executor.IndexUpsertExecutor",
    InvokeEmbedding: "qtype.interpreter.executors.invoke_embedding_executor.InvokeEmbeddingExecutor",
    InvokeFlow: "qtype.interpreter.executors.invoke_flow_executor.InvokeFlowExecutor",
    InvokeTool: "qtype.interpreter.executors.invoke_tool_executor.InvokeToolExecutor",
    LLMInference: "qtype.interpreter.executors.llm_inference_executor.LLMInferenceExecutor",
    PromptTemplate: "qtype.interpreter.executors.prompt_template_executor.PromptTemplateExecutor",
    SQLSource: "qtype.interpreter.executors.sql_source_executor.SQLSourceExecutor",
    VectorSearch: "qtype.interpreter.executors.vector_search_executor.VectorSearchExecutor",
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
    executor_path = EXECUTOR_REGISTRY.get(type(step))
    if not executor_path:
        raise ValueError(
            f"No executor found for step type: {type(step).__name__}"
        )

    # Lazy-load the executor class
    module_path, class_name = executor_path.rsplit(".", 1)
    import importlib

    module = importlib.import_module(module_path)
    executor_class = getattr(module, class_name)

    # This assumes the constructor takes the step, context, then dependencies
    return executor_class(step, context, **dependencies)
