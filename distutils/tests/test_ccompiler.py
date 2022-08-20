import os
import io
import sys
import platform
import textwrap
import sysconfig
import tempfile
from test import support

import pytest

from distutils import ccompiler
from distutils.core import Distribution
from distutils.extension import Extension
from distutils.command.build_ext import build_ext


is_windows = platform.system() == "Windows"


def _make_strs(paths):
    """
    Convert paths to strings for legacy compatibility.
    """
    if sys.version_info > (3, 8) and platform.system() != "Windows":
        return paths
    return list(map(os.fspath, paths))


@pytest.fixture
def c_file(tmp_path):
    c_file = tmp_path / 'foo.c'
    gen_headers = ('Python.h',)
    plat_headers = ('stdlib.h',) + ('Windows.h',) * is_windows
    all_headers = gen_headers + plat_headers
    headers = '\n'.join(f'#include <{header}>\n' for header in all_headers)
    payload = (
        textwrap.dedent(
            """
        #headers
        void PyInit_foo(void) {}
        """
        )
        .lstrip()
        .replace('#headers', headers)
    )
    c_file.write_text(payload)
    return c_file


def test_include_dirs(c_file):
    """
    Test basic standard include dirs to be available, including SDK on Windows.
    """
    compiler = ccompiler.new_compiler()
    python = sysconfig.get_paths()['include']
    compiler.add_include_dir(python)
    compiler.compile(_make_strs([c_file]))


@pytest.mark.skipif(not is_windows, reason="Test only on Windows")
def test_ext_include_dirs(c_file):
    """
    Test that include_dirs in an extension does not replace standard include dirs.
    """
    ext = Extension('foo', _make_strs([c_file]), include_dirs=['_nonexisting_'])
    dist = Distribution({'name': 'foo', 'ext_modules': [ext]})
    cmd = build_ext(dist)
    tmp_dir = tempfile.mkdtemp()
    cmd.build_lib = tmp_dir
    cmd.build_temp = tmp_dir

    old_stdout = sys.stdout
    if not support.verbose:
        # silence compiler output
        sys.stdout = io.StringIO()
    try:
        cmd.ensure_finalized()
        cmd.run()
    finally:
        sys.stdout = old_stdout
