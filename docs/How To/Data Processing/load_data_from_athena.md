# Load Data from Athena

Query AWS Athena databases using standard SQL with the `SQLSource` step, which supports Athena through SQLAlchemy connection strings and AWS authentication.

### QType YAML

```yaml
flows:
  - id: query-athena
    steps:
      - type: SQLSource
        id: load_sales
        connection: "awsathena+rest://:@athena.us-east-1.amazonaws.com:443/sales_db?s3_staging_dir=s3://my-results-bucket/athena-results/&work_group=primary&catalog_name=some_catalog"
        query: |
          SELECT
            product_id,
            product_name,
            total_sales
          FROM product_sales
          WHERE total_sales >= :min_sales
          ORDER BY total_sales DESC
        inputs:
          - min_sales
        outputs:
          - product_id
          - product_name
          - total_sales
```

### Explanation

- **awsathena+rest**: PyAthena SQLAlchemy dialect for accessing Athena via REST API
- **Connection string format**: `awsathena+rest://:@athena.{REGION}.amazonaws.com:443/{DATABASE}?s3_staging_dir={S3_PATH}&work_group={WORKGROUP}&catalog_name={CATALOG}"`
- **s3_staging_dir**: S3 location where Athena writes query results (required by Athena)
- **work_group**: Athena workgroup name (e.g., `primary`)
- **auth**: Reference to AWSAuthProvider for AWS credentials
- **query**: Standard SQL query with parameter substitution using `:parameter_name` syntax

## Complete Example

```yaml
--8<-- "../examples/data_processing/athena_query.qtype.yaml"
```

## See Also

- [SQLSource Reference](../../components/SQLSource.md)
- [Configure AWS Authentication](../Authentication/configure_aws_authentication.md)
- [Read Data from SQL Databases](read_sql_databases.md)
