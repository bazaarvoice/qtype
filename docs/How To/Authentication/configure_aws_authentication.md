# Configure AWS Authentication

AWS Bedrock and other AWS services require authentication, which can be configured using access keys, AWS profiles, or role assumption.

### QType YAML

```yaml
auths:
  # Method 1: AWS Profile (recommended)
  - type: aws
    id: aws_profile
    profile_name: default
    region: us-east-1
  
  # Method 2: Access Keys (for CI/CD)
  - type: aws
    id: aws_keys
    access_key_id: AKIAIOSFODNN7EXAMPLE
    secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    region: us-east-1
  
  # Method 3: Role Assumption
  - type: aws
    id: aws_role
    profile_name: base_profile
    role_arn: arn:aws:iam::123456789012:role/MyRole
    role_session_name: qtype-session
    region: us-east-1

models:
  - type: Model
    id: nova
    provider: aws-bedrock
    model_id: us.amazon.nova-micro-v1:0
    auth: aws_profile
```

### Explanation

- **type: aws**: Declares an AWS authentication provider
- **profile_name**: Uses credentials from `~/.aws/credentials` (recommended for local development)
- **access_key_id / secret_access_key**: Explicit credentials (use environment variables or secret manager)
- **session_token**: Temporary credentials for AWS STS sessions
- **role_arn**: ARN of IAM role to assume (requires base credentials via profile or keys)
- **role_session_name**: Session identifier when assuming a role
- **external_id**: External ID for cross-account role assumption
- **region**: AWS region for API calls (e.g., `us-east-1`, `us-west-2`)

## Complete Example

```yaml
--8<-- "../examples/authentication/aws_authentication.qtype.yaml"
```

## See Also

- [AWSAuthProvider Reference](../../components/AWSAuthProvider.md)
- [Use API Key Authentication](use_api_key_authentication.md)
- [Call Large Language Models](../Invoke%20Models/call_large_language_models.md)
- [Model Reference](../../components/Model.md)
