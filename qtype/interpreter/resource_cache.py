import functools
import os
from typing import Any, Callable

from cachetools import LRUCache

# Global LRU cache with a reasonable default size
_RESOURCE_CACHE_MAX_SIZE = int(os.environ.get("RESOURCE_CACHE_MAX_SIZE", 128))
_GLOBAL_RESOURCE_CACHE = LRUCache(maxsize=_RESOURCE_CACHE_MAX_SIZE)


def cached_resource(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to cache function results using a global LRU cache.

    Args:
        func: The function to cache.

    Returns:
        The wrapped function with caching.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        cache_key = (
            func.__module__,
            func.__qualname__,
            args,
            tuple(sorted(kwargs.items())),
        )
        if cache_key in _GLOBAL_RESOURCE_CACHE:
            return _GLOBAL_RESOURCE_CACHE[cache_key]
        result = func(*args, **kwargs)
        _GLOBAL_RESOURCE_CACHE[cache_key] = result
        return result

    return wrapper
