# Gather Results into a List

Combine fan-out processing results into a single list while preserving variables that have the same value across all messages (common ancestors).

### QType YAML

```yaml
variables:
  - id: processed_product
    type: text
  - id: all_processed
    type: list[text]

steps:
  - type: Collect
    id: aggregate
    inputs: [processed_product]
    outputs: [all_processed]
```

### Explanation

- **Collect**: Gathers all input values from multiple messages into a single list output
- **Common ancestors**: Only variables that have the exact same value across ALL input messages are preserved in the output message
- **Fan-out pattern**: Typically used after `Explode` to reverse the fan-out and aggregate results
- **Single output**: Always produces exactly one output message containing the aggregated list

### Understanding Common Ancestors

If you have these three messages flowing into `Collect`:

```
Message 1: {category: "Electronics", region: "US", product: "Phone", processed: "Processed: Phone"}
Message 2: {category: "Electronics", region: "US", product: "Laptop", processed: "Processed: Laptop"}
Message 3: {category: "Electronics", region: "US", product: "Tablet", processed: "Processed: Tablet"}
```

The `Collect` step will output:

```
{category: "Electronics", region: "US", all_processed: ["Processed: Phone", "Processed: Laptop", "Processed: Tablet"]}
```

Note that `product` is **not preserved** because it has different values across the messages. Only `category` and `region` (which are identical in all three messages) are included as common ancestors.

## Complete Example

```yaml
--8<-- "../examples/data_processing/collect_results.qtype.yaml"
```

Run the example:

```bash
qtype run examples/data_processing/collect_results.qtype.yaml \
  -i '{"category": "Electronics", "region": "US", "products": ["Phone", "Laptop", "Tablet"]}'
```

Output:
```
all_processed: ['Processed: Phone', 'Processed: Laptop', 'Processed: Tablet']
```

## See Also

- [Explode Collections for Fan-Out Processing](explode_collections.md)
- [Collect Reference](../../components/Collect.md)
- [Explode Reference](../../components/Explode.md)
