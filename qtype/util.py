from qtype.dsl.model import VariableTypeEnum
from datetime import date, datetime, time


VARIABLE_TO_TYPE = {
    # VariableTypeEnum.audio: bytes, # TODO: Define a proper audio type
    VariableTypeEnum.boolean: bool,  # No boolean type in enum, using Python's
    VariableTypeEnum.bytes: bytes,
    VariableTypeEnum.date: date,
    VariableTypeEnum.datetime: datetime,
    VariableTypeEnum.embedding: list[
        float
    ],  # Assuming embeddings are lists of floats
    VariableTypeEnum.int: int,
    # VariableTypeEnum.file: bytes,  # TODO: Define a proper file type
    # VariableTypeEnum.image: bytes,  # TODO: Define a proper image type
    VariableTypeEnum.float: float,
    VariableTypeEnum.text: str,
    VariableTypeEnum.time: time,
    # VariableTypeEnum.video: bytes,  # TODO: Define a proper video type
}

TYPE_TO_VARIABLE = {v: k for k, v in VARIABLE_TO_TYPE.items()}

assert len(VARIABLE_TO_TYPE) == len(TYPE_TO_VARIABLE), (
    "Variable to type mapping is not one-to-one"
)
