# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import time
from functools import lru_cache, wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")


def ttl_cache(
    seconds: int = 3600, maxsize: int = 128
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Cache a function’s return value for `seconds` seconds.

    If the function is called again within that time period, the cached value
    is returned.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @lru_cache(maxsize=maxsize)
        def wrapper(hash_: int, /, *args: P.args, **kwargs: P.kwargs) -> R:
            del hash_
            return func(*args, **kwargs)

        @wraps(func)
        def w2(*args: P.args, **kwargs: P.kwargs) -> R:
            hash_ = round(time.time() / seconds)
            return wrapper(hash_, *args, **kwargs)  # type: ignore[arg-type]  # mypy bug

        return w2

    return decorator
