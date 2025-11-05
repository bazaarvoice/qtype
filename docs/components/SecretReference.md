### SecretReference

A reference to a secret in the application's configured SecretManager.
This value is resolved at runtime by the interpreter.

- **secret_name** (`str`): The name, ID, or ARN of the secret to fetch (e.g., 'my-project/db-password').
- **key** (`str | None`): Optional key if the secret is a JSON blob or map (e.g., a specific key in a K8s secret).
