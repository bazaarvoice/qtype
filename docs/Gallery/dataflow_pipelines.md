# LLM Processing Pipelines

## Overview

An automated data processing pipeline that reads product reviews from a SQLite database and analyzes each review's sentiment using an LLM. This example demonstrates QType's dataflow capabilities with database sources, parallel LLM processing, and streaming results without requiring batch operations.

## Architecture

```mermaid
--8<-- "Gallery/dataflow_pipelines.mermaid"
```

## Complete Code

```yaml
--8<-- "../examples/data_processing/dataflow_pipelines.qtype.yaml"
```

## Key Features

- **SQLSource Step**: Database source that executes SQL queries using SQLAlchemy connection strings and emits one message per result row, enabling parallel processing of database records through downstream steps
- **PromptTemplate Step**: Template engine with curly-brace variable substitution (`{product_name}`, `{rating}`) that dynamically generates prompts from message variables for each review
- **LLMInference Step**: Processes each message independently through the language model with automatic parallelization, invoking AWS Bedrock inference for all reviews concurrently
- **Multi-record Flow**: Each database row becomes an independent FlowMessage flowing through the pipeline in parallel, carrying variables (review_id, product_name, rating, review_text) and accumulating new fields (llm_analysis) at each step
- **Message Sink**: The final step accumulates all records and writes them to an output file.

## Running the Example

### Setup

First, create the sample database with product reviews:

```bash
python examples/data_processing/create_sample_db.py
```

This generates a SQLite database with 10 sample product reviews covering various products and sentiments.

### Run the Pipeline

Process all reviews and generate the analysis with real-time progress monitoring:

```bash
qtype run -i '{"output_path":"results.parquet"}' --progress examples/data_processing/dataflow_pipelines.qtype.yaml
```

The `--progress` flag displays a live dashboard showing:
- Message throughput for each step (msg/s)
- Success/error counts
- Processing duration with visual progress bars

Example output:
```
╭─────────────────────────────────────────────────────────────────────────────── Flow Progress ───────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                             │
│  Step load_reviews                      1.6 msg/s       ▁▁▁▁▃▃▃▃▅▅▅▅████████            ✔ 10 succeeded         ✖ 0 errors       ⟳ - hits      ✗ - misses      0:00:06       │
│  Step create_prompt                     1.6 msg/s       ▁▁▁▁▃▃▃▃▅▅▅▅████████            ✔ 10 succeeded         ✖ 0 errors       ⟳ - hits      ✗ - misses      0:00:06       │
│  Step analyze_sentiment                 2.0 msg/s       ▄▄▄▄▆▆▆▆▅▅▅▅███████▁            ✔ 10 succeeded         ✖ 0 errors       ⟳ - hits      ✗ - misses      0:00:04       │
│  Step write_results                    - msg/s                                          ✔ 1 succeeded          ✖ 0 errors       ⟳ - hits      ✗ - misses      0:00:00       │
│                                                                                                                                                                             │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

You'll notice that the output shows 1 message for `write_results` and 10 for the others. That is because it is reporting the number of messages _emitted_ from each step, and `write_results` is a sink that collects all messages.

By default, QType shows a summary of the results. The final message will show:

```
2026-01-16 11:23:35,151 - INFO: ✅ Flow execution completed successfully
2026-01-16 11:23:35,151 - INFO: Processed 1 rows
2026-01-16 11:23:35,152 - INFO: 
Results summary: 1 rows, 1 columns: ['result_file']
```

To see the full output data, add the `--show-output` flag:

```bash
qtype run -i '{"output_path":"results.parquet"}' --progress --show-output examples/data_processing/dataflow_pipelines.qtype.yaml
```

This will display:

```
2026-01-16 11:23:35,152 - INFO: 
Results:
result_file: results.parquet
```

## Learn More

- [Tutorial: Your First QType Application](../Tutorials/01-first-qtype-application.md)
- [Read Data from SQL Databases](../How%20To/Data%20Processing/read_sql_databases.md)
- [Adjust Concurrency](../How%20To/Data%20Processing/adjust_concurrency.md)
