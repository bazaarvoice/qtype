### VertexAuthProvider

Google Vertex authentication provider supporting gcloud profile or service account.

- **type** (`Literal`): (No documentation available.)
- **profile_name** (`str | None`): Local gcloud profile name (if using existing CLI credentials).
- **project_id** (`str | None`): Explicit GCP project ID override (if different from profile).
- **service_account_file** (`str | None`): Path to a service account JSON key file.
- **region** (`str | None`): Vertex region (e.g., us-central1).
