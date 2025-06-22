"""
Unit tests for QType semantic validation - Section 6: Model + Embedding Rules.

This module tests model and embedding model validation rules as defined in
semantic_ir.md Section 6.
"""

import unittest

from qtype.dsl.model import (
    EmbeddingModel,
    Model,
    QTypeSpec,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class ModelRulesTest(unittest.TestCase):
    """Test Section 6: Model + Embedding Rules validation rules."""

    def test_regular_model_success(self) -> None:
        """Test that regular models pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(
                    id="gpt4",
                    provider="openai",
                    model_id="gpt-4",
                    inference_params={"temperature": 0.7, "max_tokens": 1000},
                )
            ],
        )
        validate_semantics(spec)

    def test_embedding_model_success(self) -> None:
        """Test that embedding models pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="text_embed",
                    provider="openai",
                    model_id="text-embedding-ada-002",
                    dimensions=1536,
                )
            ],
        )
        validate_semantics(spec)

    def test_embedding_model_with_inference_params_success(self) -> None:
        """Test that embedding models with inference_params pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="text_embed",
                    provider="openai",
                    model_id="text-embedding-ada-002",
                    dimensions=1536,
                    inference_params={"batch_size": 100},
                )
            ],
        )
        validate_semantics(spec)

    def test_embedding_model_no_inference_params_success(self) -> None:
        """Test that embedding models without inference_params pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="text_embed",
                    provider="openai",
                    model_id="text-embedding-ada-002",
                    dimensions=1536,
                    # No inference_params should be allowed
                )
            ],
        )
        validate_semantics(spec)

    def test_consistent_provider_naming_success(self) -> None:
        """Test that consistent provider naming across models passes validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(id="gpt4", provider="openai"),
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                ),
            ],
        )
        validate_semantics(spec)

    def test_mixed_providers_success(self) -> None:
        """Test that mixed providers across models pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(id="gpt4", provider="openai"),
                Model(id="claude", provider="anthropic"),
                EmbeddingModel(
                    id="embed_model", provider="cohere", dimensions=4096
                ),
            ],
        )
        validate_semantics(spec)

    def test_model_with_custom_model_id_success(self) -> None:
        """Test that models with custom model_id pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(
                    id="custom_gpt",
                    provider="openai",
                    model_id="ft:gpt-3.5-turbo-0613:my-org:my-model:abc123",
                )
            ],
        )
        validate_semantics(spec)

    def test_model_without_model_id_success(self) -> None:
        """Test that models without explicit model_id pass validation (id is used)."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(id="gpt-4", provider="openai"),
                EmbeddingModel(
                    id="text-embedding-ada-002",
                    provider="openai",
                    dimensions=1536,
                ),
            ],
        )
        validate_semantics(spec)

    def test_embedding_model_requires_dimensions_success(self) -> None:
        """Test that embedding models with dimensions pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="small_embed",
                    provider="openai",
                    dimensions=512,
                ),
                EmbeddingModel(
                    id="large_embed",
                    provider="openai",
                    dimensions=3072,
                ),
            ],
        )
        validate_semantics(spec)

    def test_models_with_different_inference_params_success(self) -> None:
        """Test that models with various inference parameters pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(
                    id="creative_model",
                    provider="openai",
                    inference_params={
                        "temperature": 0.9,
                        "top_p": 0.95,
                        "max_tokens": 2000,
                        "frequency_penalty": 0.5,
                        "presence_penalty": 0.2,
                    },
                ),
                Model(
                    id="deterministic_model",
                    provider="openai",
                    inference_params={"temperature": 0.0},
                ),
            ],
        )
        validate_semantics(spec)


if __name__ == "__main__":
    unittest.main()
