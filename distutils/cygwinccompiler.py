from .compilers.C import cygwin
from .compilers.C.cygwin import (
    CONFIG_H_NOTOK,
    CONFIG_H_OK,
    CONFIG_H_UNCERTAIN,
    check_config_h,
    get_msvcr,
    is_cygwincc,
)

__all__ = [
    'CONFIG_H_NOTOK',
    'CONFIG_H_OK',
    'CONFIG_H_UNCERTAIN',
    'CygwinCCompiler',
    'Mingw32Compiler',
    'check_config_h',
    'get_msvcr',
    'is_cygwincc',
]


CygwinCCompiler = cygwin.Compiler
Mingw32Compiler = cygwin.MinGW32Compiler


get_versions = None
"""
A stand-in for the previous get_versions() function to prevent failures
when monkeypatched. See pypa/setuptools#2969.
"""
