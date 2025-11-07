# Tutorial: Data Processing Pipelines

**What you'll learn:** In 15 minutes, you'll build a data processing flow that loads records from a CSV file and aggregates them. You'll learn how QType handles one-to-many operations.

**What you'll build:** A simple data pipeline that counts customer records from a CSV file.

## Before You Begin

You should have completed:
- **[Tutorial 1: Your First QType Application](01-first-qtype-application.md)** - Understanding applications, models, flows

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
     (many)          (one)
```

### Key Concepts

**Step Cardinality** - Does a step emit one result or many?
- `cardinality: one` - Takes input(s), emits 1 output per input
- `cardinality: many` - Takes input(s), emits 0...N outputs per input

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

**Key insight:** FileSource has `cardinality: many` - it takes one input (file path) and emits many outputs (one per row).

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
      - name
      - region
      - purchases
```

**What's happening:**
- We declare 5 variables for each stage of processing
- Only `file_path` is required as input (the file path)
- All four fields are returned as outputs: `stats` (aggregate summary) plus the three data fields
- The intermediate variables (`name`, `region`, `purchases`) flow between steps
- `AggregateStats` is a built-in type with success/failure counts

**Why return all fields?** This lets you see both the individual records AND the aggregate summary in the output.

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
- `cardinality: many` (implicit) - Emits one output per row
- Output variable names must match CSV column names

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

**`Aggregate` step** - Combines many items into one result
- Counts how many items flow through
- `cardinality: one` - Takes many inputs, emits 1 output
- Waits for all upstream items before computing
- Outputs `AggregateStats` with success/failure counts

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
INFO: Processed 6 input(s)
INFO: 
Results:
                                       stats     name region  purchases
0                                       None    Alice   West        5.0
1                                       None      Bob   East        3.0
2                                       None  Charlie   West        7.0
3                                       None    Diana  North        2.0
4                                       None      Eve   East        4.0
5  num_successful=5 num_failed=0 num_total=5     None   None        NaN
```

**What happened:**
1. FileSource read 5 rows from CSV
2. Each row became a FlowMessage with name, region, purchases
3. All 5 messages flowed through to Aggregate
4. Aggregate counted them and output final stats
5. You see 5 data rows (0-4) with customer info + 1 final stats row (5)

**Understanding the output:**
- **Rows 0-4:** Individual customer records with `stats=None` (data hasn't been aggregated yet)
- **Row 5:** Aggregate summary with `stats=AggregateStats(...)` and data fields as `None`/`NaN`

**Why 6 outputs?** The Aggregate step passes through all input messages (rows 0-4) and then adds one final summary message (row 5) with the stats.

---

## What You've Learned

Congratulations! You've mastered:

✅ **FileSource step** - Reading data from CSV files (also supports Parquet, JSON, JSONL)  
✅ **Aggregate step** - Counting and combining results  
✅ **Step cardinality** - Understanding one-to-many operations  
✅ **Variable naming** - Output names must match column names

---

## Understanding One-to-Many Operations

QType steps have different cardinalities:

**`cardinality: many`** - One input produces multiple outputs:
```
FileSource: 1 file path → 5 records (one per row)
```

**`cardinality: one`** - Each input produces one output:
```
Decoder: 1 string → 1 parsed object
LLMInference: 1 prompt → 1 response
```

**Many-to-one aggregation** - Multiple inputs produce one output:
```
Aggregate: 5 records → 1 summary statistic
```

This is why FileSource is so powerful - it lets you process entire datasets with a simple file path input!

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

Now that you understand data processing:

**Want to dive deeper?**
- [FileSource Reference](../components/FileSource.md) - All file formats
- [Aggregate Reference](../components/Aggregate.md) - Statistics details
- [AggregateStats Reference](../components/AggregateStats.md) - Output structure

**Try These Extensions:**

1. **Add a FileWriter:**
   - Add a `FileWriter` step after Aggregate
   - Write the stats to an output CSV file

2. **Process multiple files:**
   - Call the flow multiple times with different file paths
   - Compare counts across different datasets

3. **Add data transformation:**
   - Use Tutorial 3's FieldExtractor to filter or transform records
   - Chain multiple steps together

---

## Complete Code

**Download:** [data_processor.qtype.yaml](../../examples/data_processor.qtype.yaml)

Here's your complete application:

```yaml
id: data_processor
description: Process CSV data to extract and summarize information

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
      - name
      - region
      - purchases
    
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
      
      # Step 2: Count all records
      - id: count_records
        type: Aggregate
        inputs:
          - region
        outputs:
          - stats
          - name
          - region
          - purchases
```

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

**Q: What's the difference between `cardinality: one` and `cardinality: many`?**  
A: 
- `one` - Each input produces exactly one output (transforms, LLM calls)
- `many` - Each input can produce 0, 1, or more outputs (file reading, searches)

**Q: Why do I see multiple rows of output for Aggregate?**  
A: Aggregate passes through all input messages first (so you can see the data flowing through), then adds one final summary row with the aggregate stats.

**Q: Can FileSource read from URLs or S3?**  
A: Yes! FileSource uses fsspec, so it supports many protocols like `s3://`, `http://`, `gs://`, etc. Just provide the full URI as the file path.
