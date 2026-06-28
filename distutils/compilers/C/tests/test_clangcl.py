import os
from .. import msvc


class TestClangCLCompiler:
    def test_compiler_type(self):
        compiler = msvc.ClangCLCompiler()
        assert compiler.compiler_type == 'clangcl'

    def test_set_executables(self):
        compiler = msvc.ClangCLCompiler()
        compiler.initialize()

        cc, cc_ext = os.path.splitext(compiler.cc)
        linker, linker_ext = os.path.splitext(compiler.linker)
        lib, lib_ext = os.path.splitext(compiler.lib)
        rc, rc_ext = os.path.splitext(compiler.rc)
        mc, mc_ext = os.path.splitext(compiler.mc)
        mt, mt_ext = os.path.splitext(compiler.mt)

        assert compiler.cc == 'clang-cl' + cc_ext
        assert compiler.linker == 'lld-link' + linker_ext
        assert compiler.lib == 'llvm-lib' + lib_ext
        assert compiler.rc == 'llvm-rc' + rc_ext
        assert compiler.mc == 'llvm-ml' + mc_ext
        assert compiler.mt == 'llvm-mt' + mt_ext
