### BedrockReranker

Reranks documents using an AWS Bedrock model.

- **type** (`Literal`): (No documentation available.)
- **auth** (`Reference[AWSAuthProvider] | str | None`): AWS authorization provider for Bedrock access.
- **model_id** (`str`): Bedrock model ID to use for reranking. See https://docs.aws.amazon.com/bedrock/latest/userguide/rerank-supported.html
- **num_results** (`int | None`): Return this many results.
