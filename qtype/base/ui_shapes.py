from enum import Enum
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict as PydanticConfigDict
from pydantic import Field

from qtype.base.types import PrimitiveTypeEnum


class TextWidget(str, Enum):
    text = "text"  # Simple text widget input, default
    textarea = "textarea"  # A paragraph editor


class TextInputUI(BaseModel):
    model_config = PydanticConfigDict(extra="forbid")

    widget: TextWidget = Field(
        default=TextWidget.text,
        description="What kind of text ui to present",
    )


class FileUploadUI(BaseModel):
    model_config = PydanticConfigDict(extra="forbid")
    accept: str = Field(
        default="*/*",
        description="The mime type(s) to accept in the file upload.",
    )


UIType = Union[TextInputUI, FileUploadUI]

UI_INPUT_TO_TYPE = {
    (TextInputUI, PrimitiveTypeEnum.text),
    (FileUploadUI, PrimitiveTypeEnum.file),
}
