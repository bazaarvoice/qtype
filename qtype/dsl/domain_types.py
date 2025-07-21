from pydantic import BaseModel, ConfigDict, Field

#
# ---------------- Base Components ----------------
#


class StrictBaseModel(BaseModel):
    """Base model with extra fields forbidden."""

    model_config = ConfigDict(extra="forbid")


class Embedding(StrictBaseModel):
    """A standard, built-in representation of a vector embedding."""

    vector: list[float] = Field(
        ..., description="The vector representation of the embedding."
    )
    source_text: str | None = Field(
        None, description="The original text that was embedded."
    )
    metadata: dict[str, str] | None = Field(
        None, description="Optional metadata associated with the embedding."
    )
