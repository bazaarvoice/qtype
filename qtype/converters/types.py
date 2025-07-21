from qtype.dsl.base_types import PrimitiveTypeEnum

"""
Mapping of QType primitive types to Python types for internal representations.
"""
PRIMITIVE_TO_PYTHON_TYPE = {
    PrimitiveTypeEnum.audio: bytes,
    PrimitiveTypeEnum.boolean: bool,
    PrimitiveTypeEnum.bytes: bytes,
    PrimitiveTypeEnum.date: str,  # Use str for date representation
    PrimitiveTypeEnum.datetime: str,  # Use str for datetime representation
    PrimitiveTypeEnum.int: int,
    PrimitiveTypeEnum.file: bytes,  # Use bytes for file content
    PrimitiveTypeEnum.float: float,
    PrimitiveTypeEnum.image: bytes,  # Use bytes for image data
    PrimitiveTypeEnum.number: float,  # Use float for number representation
    PrimitiveTypeEnum.text: str,
    PrimitiveTypeEnum.time: str,  # Use str for time representation
    PrimitiveTypeEnum.video: bytes,  # Use bytes for video data
}
