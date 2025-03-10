from .compilers.C import msvc
from .compilers.C.msvc import PLAT_SPEC_TO_RUNTIME

__all__ = ["PLAT_SPEC_TO_RUNTIME", "MSVCCompiler"]

MSVCCompiler = msvc.Compiler
