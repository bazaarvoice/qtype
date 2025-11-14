import hashlib
import pathlib

import diskcache as dc

from qtype.base.types import CacheConfig
from qtype.interpreter.types import FlowMessage


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


def cache_key(message: FlowMessage) -> str:
    """Generates a cache key based on the message content."""

    text = message.model_dump_json()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
