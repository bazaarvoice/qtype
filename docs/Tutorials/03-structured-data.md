# Working with Types and Structured Data

**Time:** 25 minutes  
**Prerequisites:** [Tutorial 1: Your First QType Application](01-first-qtype-application.md)  
**Example:** [`03_structured_data.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/tutorials/03_structured_data.qtype.yaml)

**What you'll learn:**

* Define custom types for your domain
* Parse LLM JSON responses into structured data
* Build typed objects from extracted fields
* Work with list types

**What you'll build:** An application that analyzes product reviews and extracts structured sentiment data including ratings, confidence scores, and key points.

---

## Background: Why Custom Types?

So far you've worked with simple `text` types. But real applications need structure:

- **Domain models** - Product reviews, user profiles, search results
- **Validation** - Ensure data has required fields
- **Type safety** - Catch errors before runtime
- **Composability** - Build complex types from simpler ones

QType lets you define **CustomTypes** to model your domain, just like you'd define classes in Python.

---

## Part 1: Define Your Custom Type (5 minutes)

### Create Your Application File

Create `03_structured_data.qtype.yaml`:

```yaml
id: review_sentiment_analyzer
description: |
  Analyzes a product review to extract structured sentiment insights.
  Demonstrates custom types and structured data extraction.
```

---

### Define a CustomType

Before the `models:` section, add a `types:` section:

```yaml
types:
  - id: ReviewSentiment
    description: Structured sentiment analysis of a review
    properties:
      sentiment: text
      confidence: float
      key_points: list[text]
      rating: int
```

**What this means:**

**`types:` section** - Where you define custom data structures

**`properties:`** - The fields your type contains:
- `sentiment: text` - A simple text field
- `confidence: float` - A decimal number (0.0-1.0)
- `key_points: list[text]` - A list of strings (new!)
- `rating: int` - An integer (1-5 star rating)

**List types** use the syntax `list[element_type]`. Examples:
- `list[text]` - List of strings
- `list[int]` - List of integers  
- `list[ReviewSentiment]` - List of custom types

---

### Add Model Configuration

```yaml
models:
  - type: Model
    id: analyzer_model
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 512
```

**Check your work:**

```bash
qtype validate 03_structured_data.qtype.yaml
```

Should pass ✅

---

## Part 2: Build the Analysis Flow (10 minutes)

### Define Flow Variables

Add the flow structure:

```yaml
flows:
  - id: analyze_review
    description: Analyzes a single review and extracts structured sentiment
    inputs:
      - review_text
    outputs:
      - result

    variables:
      - id: review_text
        type: text
      - id: raw_llm_response
        type: text
      - id: llm_response
        type: text
      - id: sentiment
        type: text
      - id: confidence
        type: float
      - id: key_points
        type: list[text]
      - id: rating
        type: int
      - id: result
        type: ReviewSentiment
```

**What's new:**

**Multiple variable types** - Notice we have:
- Simple types (`text`, `float`, `int`)
- List type (`list[text]`)
- Custom type (`ReviewSentiment`)

**Why so many variables?** Each step transforms data from one form to another. This explicit data flow makes debugging easier and documents how information moves through your application.

---

### Step 1: Create the Analysis Prompt

Add the first step under `steps:`:

```yaml
    steps:
      # Step 1: Create analysis prompt
      - id: analysis_prompt
        type: PromptTemplate
        template: |
          Analyze this product review and extract structured information.

          Review: {{review_text}}

          Respond with ONLY valid JSON, no other text or markdown. Use this exact structure:
          {{{{
            "sentiment": "positive|negative|neutral|mixed",
            "confidence": 0.95,
            "key_points": ["point 1", "point 2"],
            "rating": 4
          }}}}

          Where:
          - sentiment: overall sentiment (positive/negative/neutral/mixed)
          - confidence: your confidence score (0.0-1.0)
          - key_points: 2-3 main points from the review
          - rating: estimated star rating 1-5 based on the tone
          
          Return ONLY the JSON object, nothing else.
        inputs:
          - review_text
        outputs:
          - raw_llm_response
```

**Key technique - Escaping braces:**

Notice `{{` and `}}` in the template? QType uses Python's `.format()` method where `{variable}` is a placeholder. To include literal curly braces in the output, you must double them:
- `{{` → outputs `{`
- `}}` → outputs `}`

So to output the JSON structure, we use `{{ ... }}` which renders as `{ ... }` in the actual prompt.

**Why "ONLY valid JSON"?** LLMs often add explanatory text or wrap JSON in markdown code fences. Being explicit reduces these issues.

---

### Step 2: Run LLM Inference

```yaml
      # Step 2: Run LLM inference
      - id: analyze
        type: LLMInference
        model: analyzer_model
        inputs:
          - raw_llm_response
        outputs:
          - llm_response
```

**LLMInference step** sends the prompt to your model and returns the response as text. Simple and familiar from Tutorial 1.

---

### Step 3: Parse JSON with Decoder

Here's the new step type:

```yaml
      # Step 3: Parse the JSON response and build the ReviewSentiment object
      # Decoder converts the JSON string into structured data
      - id: parse_and_build
        type: Decoder
        format: json
        inputs:
          - llm_response
        outputs:
          - sentiment
          - confidence
          - key_points
          - rating
```

**What Decoder does:**

**`format: json`** - Tells QType to parse as JSON (also supports `xml`)

**Multiple outputs** - Each output name must match a field in the JSON:
```json
{
  "sentiment": "positive",    ← goes to sentiment variable
  "confidence": 0.95,          ← goes to confidence variable
  "key_points": [...],         ← goes to key_points variable
  "rating": 4                  ← goes to rating variable
}
```

**Smart parsing:**
- Automatically strips markdown code fences (````json`)
- Validates JSON syntax
- Maps JSON types to QType types (string→text, number→float/int, array→list)
- Raises clear errors if fields are missing or malformed

**Check your work:**

```bash
qtype validate 03_structured_data.qtype.yaml
```

---

### Step 4: Construct the Typed Object

Final step - convert individual fields into your custom type:

```yaml
      # Step 4: Construct a ReviewSentiment object
      # Construct builds typed objects from the decoded fields
      - id: build_result
        type: Construct
        output_type: ReviewSentiment
        field_bindings:
          sentiment: sentiment
          confidence: confidence
          key_points: key_points
          rating: rating
        inputs:
          - sentiment
          - confidence
          - key_points
          - rating
        outputs:
          - result
```

**What Construct does:**

**`output_type: ReviewSentiment`** - Specifies which custom type to build

**`field_bindings:`** - Maps type field names to input variables:
```yaml
field_bindings:
  <property_name>: <variable_name>
```

In this case, names match (`sentiment: sentiment`), but you could use different names:
```yaml
field_bindings:
  sentiment: analyzed_sentiment  # Maps analyzed_sentiment variable to sentiment property
```

**Why Construct?** It validates that:
- All required properties are provided
- Types match (float for confidence, int for rating, etc.)
- The result is a valid `ReviewSentiment` instance

This catches errors early rather than failing later in your application.

**Final validation:**

```bash
qtype validate 03_structured_data.qtype.yaml
```

Should pass ✅

---

## Part 3: Test Your Application (5 minutes)

### Run It!

```bash
qtype run -i '{"review_text":"These headphones are amazing! Great sound quality and super comfortable. Battery lasts all day."}' --show-output 03_structured_data.qtype.yaml
```

**Expected output:**

```json
{
  "result": {
    "sentiment": "positive",
    "confidence": 0.95,
    "key_points": [
      "Great sound quality",
      "Super comfortable",
      "Long battery life"
    ],
    "rating": 5
  }
}
```

---

### Try Different Reviews

```bash
# Negative review
qtype run -i '{"review_text":"Terrible product. Broke after one week and customer service was unhelpful."}' 03_structured_data.qtype.yaml

# Mixed review
qtype run -i '{"review_text":"Good sound but uncomfortable after an hour. Battery is okay but not great."}' 03_structured_data.qtype.yaml
```

Notice how the LLM adapts its analysis while maintaining the structured format!

---

## Part 4: Understanding the Data Flow (5 minutes)

### The Complete Pipeline

Here's what happens when you run the application:

```
1. User Input (text)
   "These headphones are amazing!"
   ↓

2. PromptTemplate
   Creates prompt with JSON format instructions
   ↓

3. LLMInference  
   Sends to model → Returns JSON string
   ↓

4. Decoder
   Parses JSON string → Extracts individual fields
   {sentiment: "positive", confidence: 0.95, ...}
   ↓

5. Construct
   Builds ReviewSentiment object from fields
   ReviewSentiment(sentiment="positive", confidence=0.95, ...)
   ↓

6. Output (ReviewSentiment)
   Validated, typed data ready for downstream use
```

**Key insight:** Each step has a single, focused responsibility:
- **PromptTemplate** - Format instructions
- **LLMInference** - Get AI response
- **Decoder** - Parse structured data
- **Construct** - Validate and type

This separation makes each step testable and reusable.

**Note:** You could simplify this by having the LLM return `{"result": {...}}` and using Decoder to output directly to a `ReviewSentiment` variable, skipping the Construct step. However, this tutorial demonstrates both steps separately so you understand when to use each:
- **Decoder** - When you need to parse text and extract individual fields
- **Construct** - When you need to build typed objects from already-extracted data

In practice, use the approach that best fits your use case.

---

### Error Handling

What happens if the LLM returns invalid JSON?

**Decoder will fail** with a clear error:
```
Invalid JSON input: Expecting ',' delimiter: line 2 column 5 (char 45)
```

**What if a field is missing?**
```
Output variable 'confidence' not found in decoded result
```

**What if a type is wrong?**
```
Cannot construct ReviewSentiment: field 'rating' expects int, got str
```

These explicit errors help you debug issues quickly. In production, you might add retry logic or fallback values.

---

## What You've Learned

Congratulations! You've mastered:

✅ **CustomType definition** - Modeling your domain with structured types  
✅ **List types** - Working with `list[text]` and other collections  
✅ **Decoder step** - Parsing JSON into individual typed fields  
✅ **Construct step** - Building validated custom type instances  
✅ **Field Bindings** - Connecting variables to type properties  
✅ **Type safety** - Catching errors early with validation  

---

## Next Steps

**Reference the complete example:**

- [`03_structured_data.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/tutorials/03_structured_data.qtype.yaml) - Full working example

**Learn more:**

- [Tutorial: Tools and Function Calling](04-tools-and-function-calling.md)
- [CustomType Reference](../components/CustomType.md)
- [Decoder Reference](../components/Decoder.md)

---

## Common Questions

**Q: Can I nest custom types?**  
A: Yes! A CustomType property can be another CustomType:
```yaml
types:
  - id: Address
    properties:
      street: text
      city: text
  - id: User
    properties:
      name: text
      address: Address  # Nested custom type
```

**Q: What if the LLM returns extra fields not in my type?**  
A: Extra fields are ignored. Decoder only extracts the fields you've specified in `outputs:`.

**Q: Can Decoder output the entire JSON as one variable?**  
A: Not directly. Decoder maps JSON fields to individual outputs. If you need the whole JSON, use `type: any` in your variable and skip Decoder.

**Q: When should I use Decoder vs FieldExtractor?**  
A: Use **Decoder** when you have a JSON/XML string to parse. Use **FieldExtractor** when you already have structured data and need to extract specific fields using JSONPath (covered in advanced tutorials).

**Q: Can I make properties optional?**  
A: Yes! Mark variables as optional using the `?` suffix (e.g., `type: text?`). Optional variables can be unset, `None`, or have a value. This is useful when extracting fields that may not always be present. See [Use Optional Variables](../How%20To/Language%20Features/use_optional_variables.md).
