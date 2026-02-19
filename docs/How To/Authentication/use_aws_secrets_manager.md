# Store Secrets in AWS Secrets Manager

Avoid hardcoding API keys and passwords in your YAML by storing them in AWS Secrets Manager. QType resolves `SecretReference` values at runtime using the configured `secret_manager`.

### QType YAML

```yaml
auths:
  # AWS credentials used to access Secrets Manager itself
  - type: aws
    id: aws_auth
    region: us-east-1

  # API key resolved from Secrets Manager at runtime
  - type: api_key
    id: my-api-auth
    api_key:
      secret_name: my-project/api-key

# Declare the secret manager backed by AWS
secret_manager:
  id: aws-secret-manager
  type: aws_secret_manager
  auth: aws_auth
```

### Explanation

- **secret_manager**: Top-level application block that configures the secret backend
- **type: aws_secret_manager**: Uses AWS Secrets Manager as the secret store
- **auth**: References an `AWSAuthProvider` used to authenticate with Secrets Manager (must not itself use secret references)
- **secret_name**: The name, ID, or ARN of the secret in AWS Secrets Manager
- **key**: Optional — if the secret is a JSON object, extracts a specific key (e.g., `key: api_key`)

### Creating the Secret

```bash
aws secretsmanager create-secret \
  --name my-project/api-key \
  --secret-string "your-api-key-value" \
  --region us-east-1
```

### Using a JSON Secret with Key Extraction

If a single secret stores multiple values as a JSON object:

```bash
aws secretsmanager create-secret \
  --name my-project/credentials \
  --secret-string '{"api_key": "sk-abc123", "space_id": "xyz"}' \
  --region us-east-1
```

```yaml
  - type: api_key
    id: my-api-auth
    api_key:
      secret_name: my-project/credentials
      key: api_key           # Extract only the api_key field
```

## See Also

- [Fields That Accept Secret References](../../Reference/secret-reference-fields.md)
- [Configure AWS Authentication](configure_aws_authentication.md)
- [Use API Key Authentication](use_api_key_authentication.md)
