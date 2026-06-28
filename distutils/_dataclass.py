# This is a private module, but setuptools has the explicit permission to use it.
from __future__ import annotations

import warnings
from dataclasses import dataclass, fields
from functools import wraps
from typing import TypeVar

from .compat.py310 import dataclass_transform

_T = TypeVar("_T", bound=type)


@dataclass_transform()
def lenient_dataclass(**dc_kwargs):
    """
    Problem this class intends to solve:
    - We need to modify __init__ so to achieve backwards compatibility
      and keep allowing arbitrary keywords to be ignored
    - But we don't want to throw away the dataclass-generated __init__
      specially because we don't want to have to redefine all the typing
      for the function arguments

    If/when lenient behaviour and backward compatibility are no longer needed,
    the whole customization can be removed.
    A regular ``dataclass`` could be used instead.
    """

    @wraps(dataclass)
    def _wrap(cls: _T) -> _T:
        cls = dataclass(**dc_kwargs)(cls)
        # Allowed field names in order
        safe = tuple(f.name for f in fields(cls))
        orig_init = cls.__init__

        @wraps(orig_init)
        def _wrapped_init(self, *args, **kwargs):
            extra = {repr(k): kwargs.pop(k) for k in tuple(kwargs) if k not in safe}
            if extra:
                msg = f"""
                Please remove unknown `{cls.__name__}` options: {','.join(extra)}
                this kind of usage is deprecated and may cause errors in the future.
                """
                warnings.warn(msg)

            # Ensure default values (e.g. []) are used instead of None:
            positional = {k: v for k, v in zip(safe, args) if v is not None}
            keywords = {k: v for k, v in kwargs.items() if v is not None}
            return orig_init(self, **positional, **keywords)

        cls.__init__ = _wrapped_init
        return cls

    return _wrap
