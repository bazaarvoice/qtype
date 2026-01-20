# Fan-Out Collections with Explode

Transform a single list input into multiple outputs, one per item, enabling parallel processing of collection elements.

### QType YAML

```yaml
steps:
  - type: Explode
    id: fan_out
    inputs:
      - items      # Variable of type list[T]
    outputs:
      - item       # Variable of type T
```

### Explanation

- **Explode**: Takes a single list and yields one output message per item
- **inputs**: Must be a single variable of type `list[T]`
- **outputs**: Single variable of the item type `T` (unwrapped from the list)
- **Fan-out pattern**: Each item is processed independently by downstream steps

## Complete Example

```yaml
--8<-- "../examples/data_processing/explode_items.qtype.yaml"
```

**Run it:**
```bash
qtype run examples/data_processing/explode_items.qtype.yaml \
  -i '{"items": ["apple", "banana", "cherry"]}'
```

## See Also

- [Aggregate Data using Collect](./aggregate_data.md)
- [Explode Reference](../../components/Explode.md)
- [Adjust Concurrency](./adjust_concurrency.md)
