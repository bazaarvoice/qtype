# Fields That Accept Secret References

Any field typed as `str | SecretReference` can be supplied either as a plain string or as a reference to a secret in the configured [`secret_manager`](../components/AWSSecretManager.md). The secret is resolved at runtime.

## Syntax

```yaml
field_name:
  secret_name: my-project/my-secret   # Name, ID, or ARN
  key: optional_json_key              # Only needed for JSON-object secrets
```

## Secret-Capable Fields

| Component | Field | Description |
|-----------|-------|-------------|
| `APIKeyAuthProvider` | `api_key` | API key passed as a header or query parameter |
| `BearerTokenAuthProvider` | `token` | Bearer token for Authorization header |
| `OAuth2AuthProvider` | `client_secret` | OAuth2 client secret |
| `AWSAuthProvider` | `access_key_id` | AWS access key ID |
| `AWSAuthProvider` | `secret_access_key` | AWS secret access key |
| `AWSAuthProvider` | `session_token` | AWS STS session token (temporary credentials) |
| `SQLSource` | `connection` | SQLAlchemy connection string (contains credentials) |
| `TelemetrySink` | `endpoint` | Telemetry collector URL (if it contains auth tokens) |

## Example

```yaml
auths:
  - type: api_key
    id: openai-auth
    api_key:
      secret_name: my-project/openai-key

  - type: aws
    id: aws-auth
    access_key_id:
      secret_name: my-project/aws-creds
      key: access_key_id
    secret_access_key:
      secret_name: my-project/aws-creds
      key: secret_access_key
    region: us-east-1
```

## See Also

- [Store Secrets in AWS Secrets Manager](../How%20To/Authentication/use_aws_secrets_manager.md)
- [Configure AWS Authentication](../How%20To/Authentication/configure_aws_authentication.md)
