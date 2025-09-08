from datetime import date, datetime, time

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
    PrimitiveTypeEnum.text: str,
    PrimitiveTypeEnum.time: str,  # Use str for time representation
    PrimitiveTypeEnum.video: bytes,  # Use bytes for video data
}

PYTHON_TYPE_TO_PRIMITIVE_TYPE = {
    bytes: PrimitiveTypeEnum.file,
    bool: PrimitiveTypeEnum.boolean,
    str: PrimitiveTypeEnum.text,
    int: PrimitiveTypeEnum.int,
    float: PrimitiveTypeEnum.float,
    date: PrimitiveTypeEnum.date,
    datetime: PrimitiveTypeEnum.datetime,
    time: PrimitiveTypeEnum.time,
    # TODO: decide on internal representation for images, video, and audio, or use annotation/hinting
}

# def create_custom_type(model_cls: Type[BaseModel],) -> CustomType:
#     """
#     Create a CustomType from a Pydantic BaseModel.

#     Args:
#         type: The Pydantic BaseModel class.

#     Returns:
#         A CustomType instance representing the model.
#     """

#     properties = {}
#     for field_name, field_info in model_cls.model_fields.items():
#         # Use the annotation (the type hint) for the field
#         field_type = field_info.annotation
#         if field_type is None:
#             raise TypeError(
#                 f"Field '{field_name}' in '{model_name}' must have a type hint."
#             )
#         origin = get_origin(field_type)

#         if origin is Union:
#             # Assume the union means it's optional


#     return CustomType(
#         id=type.__name__,
#         properties={
#             name: python_type_to_variable_type(field.type_)
#             for name, field in type.__fields__.items()
#         },
#     )
