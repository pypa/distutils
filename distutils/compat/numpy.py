# required for older numpy versions on Pythons prior to 3.12; see pypa/setuptools#4876

__lazy_modules__ = {f"{(__spec__.parent or '').rsplit('.', 1)[0]}.compilers.C.base"}

from ..compilers.C.base import _default_compilers, compiler_class  # noqa: F401
