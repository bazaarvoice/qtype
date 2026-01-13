# Read Data from SQL Databases

Query relational databases and process results row-by-row using the `SQLSource` step, which supports any database accessible via SQLAlchemy connection strings.

### QType YAML

```yaml
steps:
  - type: SQLSource
    id: load_reviews
    connection: "sqlite:///data/reviews.db"
    query: |
      SELECT
        review_id,
        product_name,
        rating,
        review_text
      FROM product_reviews
      WHERE rating >= 4
      ORDER BY review_id
    outputs:
      - review_id
      - product_name
      - rating
      - review_text
```

### Explanation

- **SQLSource**: Step type that executes SQL queries and emits one message per database row
- **connection**: SQLAlchemy-format connection string (e.g., `sqlite:///path.db`, `postgresql://user:pass@host/db`)
- **query**: SQL query to execute; column names must match output variable IDs
- **outputs**: Variables to populate from query result columns (order must match SELECT clause)
- **auth**: Optional reference to AuthorizationProvider for database credentials

## Complete Example

```yaml
--8<-- "../examples/data_processing/dataflow_pipelines.qtype.yaml"
```

## See Also

- [SQLSource Reference](../../components/SQLSource.md)
- [FileSource Reference](../../components/FileSource.md)
- [Tutorial: Working with Types and Structured Data](../../Tutorials/working_with_types_and_structured_data.md)
- [Example: Dataflow Pipeline](../../Gallery/Data%20Processing/dataflow_pipelines.md)
