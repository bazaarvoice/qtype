import hashlib
import json
import pathlib
from typing import Any

import diskcache as dc
from pydantic import BaseModel
from pydantic.json import pydantic_encoder

from qtype.base.types import CacheConfig
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Step


def create_cache(config: CacheConfig | None, step_id: str) -> dc.Cache | None:
    if config is None:
        return None
    cache_dir = pathlib.Path(config.directory)
    if config.namespace:
        cache_dir = cache_dir / config.namespace
    cache_dir = cache_dir / step_id / config.version

    return dc.Cache(
        directory=str(cache_dir),
        size_limit=0,  # 0 = unlimited
        eviction_policy="none",  # disables auto-eviction
    )


def cache_key(message: FlowMessage, step: Step) -> str:
    """Generates a cache key based on the message content."""

    inputs = {}
    for var in step.inputs:
        if var.id in message.variables:
            value = message.variables[var.id]
            if isinstance(value, BaseModel):
                inputs[var.id] = value.model_dump()
            else:
                inputs[var.id] = value
        else:
            raise ValueError(
                f"Input variable '{var.id}' not found in message -- caching can not be performed."
            )
    input_str = json.dumps(inputs, sort_keys=True, default=pydantic_encoder)
    return hashlib.sha256(input_str.encode("utf-8")).hexdigest()


def to_cache_value(message: FlowMessage, step: Step) -> dict[str, Any]:
    """Converts a FlowMessage to a serializable cache value."""
    if message.is_failed():
        return {"FlowMessage.__error__": message.error}
    else:
        outputs = {}
        for var in step.outputs:
            if var.id in message.variables:
                outputs[var.id] = message.variables[var.id]
            else:
                raise ValueError(
                    f"Output variable '{var.id}' not found in message -- caching can not be performed."
                )
        return outputs


def from_cache_value(
    cache_value: dict[str, Any], message: FlowMessage
) -> FlowMessage:
    """Reconstructs a FlowMessage from cached output values."""
    if "FlowMessage.__error__" in cache_value:
        msg = message.model_copy(deep=True)
        msg.error = cache_value["FlowMessage.__error__"]
        return msg
    else:
        return message.copy_with_variables(cache_value)
