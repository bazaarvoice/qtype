# Data Processing Pipelines

**Time:** 15 minutes  
**Prerequisites:** [Tutorial 1: Build Your First QType Application](01-first-qtype-application.md)  
**Example:** [`data_processor.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/data_processor.qtype.yaml)

**What you'll learn:** Build a data processing flow that loads records from a CSV file and aggregates them. You'll learn how QType handles one-to-many operations.

**What you'll build:** A simple data pipeline that counts customer records from a CSV file.

## Before You Begin

You should have completed:

- **[Tutorial 1: Build Your First QType Application](01-first-qtype-application.md)** - Understanding applications, models, flows

Make sure you have:

- QType installed: `pip install qtype[interpreter]`
- A text editor
- 15 minutes

---

## Understanding Data Processing in QType

So far, you've built applications that process one request at a time:

- Tutorial 1: One question → one answer
- Tutorial 2: One message → one response  
- Tutorial 3: Get time → calculate difference → return result

Today you'll work with **data pipelines** that process multiple records:

```
Load CSV file → Count records
   (stream)         (summary)
```

### Key Concepts

**Streaming Processing** - Processing multiple records

- FileSource reads the file and emits one record at a time
- Each record flows through the pipeline as it's read
- Aggregate collects all records and produces a summary

---

## Part 1: Understanding the Pipeline (5 minutes)

### The Flow We'll Build

```
┌──────────────┐
│  CSV File    │
│  (5 records) │
└──────┬───────┘
       │ FileSource (emits 5 items)
       ↓
┌──────────────┐
│  Records     │
│  (streaming) │
└──────┬───────┘
       │ Aggregate (counts all)
       ↓
┌──────────────┐
│ Total: 5     │
└──────────────┘
```

**Key insight:** FileSource emits multiple outputs (one per row) from a single input (file path).

---

### Create Sample Data

First, let's create test data. Create a folder called `examples/data/`:

```bash
mkdir -p examples/data
```

Create `examples/data/customers.csv`:

```csv
name,region,purchases
Alice,West,5
Bob,East,3
Charlie,West,7
Diana,North,2
Eve,East,4
```

**Note:** This is standard CSV format with a header row and data rows.

---

## Part 2: Build the Pipeline (5 minutes)

### Create Your Application

Create `examples/data_processor.qtype.yaml`:

```yaml
id: data_processor
description: Process CSV data to extract and summarize information
```

---

### Define Your Flow

Add a flow that declares all the variables we'll use:

```yaml
flows:

- type: Flow
    id: process_customers
    description: Load customer data and count records
    
    variables:

- id: file_path
        type: text
      - id: name
        type: text
      - id: region
        type: text
      - id: purchases
        type: int
      - id: stats
        type: AggregateStats
    
    inputs:

- file_path
    
    outputs:

- stats
```

**What's happening:**

- We declare 5 variables for each stage of processing
- Only `file_path` is required as input (the file path)
- Only `stats` is returned as output (the aggregate summary)
- The intermediate variables (`name`, `region`, `purchases`) flow between steps
- `AggregateStats` is a built-in type with success/failure counts

**Check your work:**

1. Validate: `uv run qtype validate examples/data_processor.qtype.yaml`
2. Should pass ✅

---

### Step 1: Load CSV Data

Add the first step to read the file:

```yaml
    steps:
      # Step 1: Read CSV file (emits many records, one per row)
      - id: load_file
        type: FileSource
        path: file_path
        inputs:

- file_path
        outputs:

- name
          - region
          - purchases
```

**New concepts:**

**`FileSource` step** - Reads data from files

- `path: file_path` - Reference to variable containing file path
- Automatically detects format from file extension (`.csv`, `.parquet`, `.json`, `.jsonl`)
- Emits one output per row (streaming)
- Output variable names should match CSV column names

**How it works:**

```
Input: file_path = "examples/data/customers.csv"
Process: Read file row by row
Output: 5 separate records with name, region, purchases
```

**Important:** The CSV columns (`name`, `region`, `purchases`) must match the output variable names exactly.

---

### Step 2: Aggregate Results

Add a step to count all the records:

```yaml
      # Step 2: Count all records
      - id: count_records
        type: Aggregate
        inputs:

- region
        outputs:

- stats
```

**`Aggregate` step** - Combines many items into one summary

- Counts how many items flow through
- Waits for all upstream items before computing
- Emits a single summary with `AggregateStats` containing success/failure counts

**What this does:**

```
Input:  5 records flow through (one at a time)
Output: stats = AggregateStats(num_successful=5, num_failed=0, num_total=5)
```

**Check your work:**

1. Validate: `uv run qtype validate examples/data_processor.qtype.yaml`
2. Should pass ✅

---

## Part 3: Run Your Pipeline (5 minutes)

### Test It!

Run the flow with your test data:

```bash
uv run qtype run -i '{"file_path":"examples/data/customers.csv"}' examples/data_processor.qtype.yaml
```

**Expected output:**

```
INFO: Executing workflow from examples/data_processor.qtype.yaml
INFO: ✅ Flow execution completed successfully
INFO: Processed 1 input(s)
INFO: 
Results:
                                     stats
0  num_successful=5 num_failed=0 num_total=5
```

**What happened:**

1. FileSource read 5 rows from CSV
2. Each row became a FlowMessage with name, region, purchases
3. All 5 messages streamed through to Aggregate
4. Aggregate counted them and emitted a single final summary with stats

**Understanding the output:**

The Aggregate step produces one summary result with statistics about the data that flowed through:

- `num_successful=5` - 5 records processed successfully
- `num_failed=0` - 0 records had errors
- `num_total=5` - 5 total records processed

---

## What You've Learned

Congratulations! You've mastered:

✅ **FileSource step** - Reading data from CSV files (also supports Parquet, JSON, JSONL)  
✅ **Aggregate step** - Counting and combining results  
✅ **Streaming data** - Processing records one at a time  
✅ **Variable naming** - Output names must match column names

---

## Compare: Conversational vs Complete Flows

| Feature | Conversational (Tutorial 2) | Complete (Tutorial 4) |
|---------|----------------------------|----------------------|
| **Interface** | `interface: {type: Conversational}` | Default (no interface specified) |
| **Memory** | Required (stores chat history) | Not used |
| **Input/Output** | One message at a time | Can process multiple records |
| **Use Case** | Chat, assistants | Data processing, ETL |
| **Testing** | `qtype serve` (web UI) | `qtype run` (command line) |

---

## Next Steps

**Reference the complete example:**

- [`data_processor.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/data_processor.qtype.yaml) - Full working example

**Learn more:**

- [FileSource Reference](../components/FileSource.md) - All file formats
- [Aggregate Reference](../components/Aggregate.md) - Statistics details
- [AggregateStats Reference](../components/AggregateStats.md) - Output structure

---

## Common Questions

**Q: What file formats are supported?**  
A: CSV, Parquet, JSON, and JSONL. The format is automatically detected from the file extension.

**Q: Can I rename columns?**  
A: Not currently. Output variable names must match the column names in the file exactly.

**Q: How do I filter or transform data?**  
A: Use the `FieldExtractor` step (from Tutorial 3) or `Decoder` step to parse and transform the data before aggregating.

**Q: How do I process data from databases?**  
A: Use `SQLSource` step instead of `FileSource`. It works similarly but connects to databases and executes SQL queries.

**Q: How does streaming work with FileSource?**  
A: FileSource reads and emits records one at a time rather than loading the entire file into memory. This allows processing large files efficiently.

**Q: What does Aggregate output?**  
A: Aggregate outputs a single summary message with `AggregateStats` containing counts of successful, failed, and total messages that flowed through the step.

**Q: Can FileSource read from URLs or S3?**  
A: Yes! FileSource uses fsspec, so it supports many protocols like `s3://`, `http://`, `gs://`, etc. Just provide the full URI as the file path.
