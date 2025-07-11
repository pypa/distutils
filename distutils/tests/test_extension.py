"""Tests for distutils.extension."""

import os
import pathlib
import re
import warnings
from dataclasses import dataclass, field
from distutils.extension import Extension, read_setup_file
from typing import TYPE_CHECKING

import pytest


class TestExtension:
    def test_read_setup_file(self):
        # trying to read a Setup file
        # (sample extracted from the PyGame project)
        setup = os.path.join(os.path.dirname(__file__), 'Setup.sample')

        exts = read_setup_file(setup)
        names = [ext.name for ext in exts]
        names.sort()

        # here are the extensions read_setup_file should have created
        # out of the file
        wanted = [
            '_arraysurfarray',
            '_camera',
            '_numericsndarray',
            '_numericsurfarray',
            'base',
            'bufferproxy',
            'cdrom',
            'color',
            'constants',
            'display',
            'draw',
            'event',
            'fastevent',
            'font',
            'gfxdraw',
            'image',
            'imageext',
            'joystick',
            'key',
            'mask',
            'mixer',
            'mixer_music',
            'mouse',
            'movie',
            'overlay',
            'pixelarray',
            'pypm',
            'rect',
            'rwobject',
            'scrap',
            'surface',
            'surflock',
            'time',
            'transform',
        ]

        assert names == wanted

    def test_extension_init(self):
        # the first argument, which is the name, must be a string
        with pytest.raises(TypeError):
            Extension(1, [])
        ext = Extension('name', [])
        assert ext.name == 'name'

        # the second argument, which is the list of files, must
        # be an iterable of strings or PathLike objects, and not a string
        with pytest.raises(TypeError):
            Extension('name', 'file')
        with pytest.raises(TypeError):
            Extension('name', ['file', 1])
        ext = Extension('name', ['file1', 'file2'])
        assert ext.sources == ['file1', 'file2']
        ext = Extension('name', [pathlib.Path('file1'), pathlib.Path('file2')])
        assert ext.sources == ['file1', 'file2']

        # any non-string iterable of strings or PathLike objects should work
        ext = Extension('name', ('file1', 'file2'))  # tuple
        assert ext.sources == ['file1', 'file2']
        ext = Extension('name', {'file1', 'file2'})  # set
        assert sorted(ext.sources) == ['file1', 'file2']
        ext = Extension('name', iter(['file1', 'file2']))  # iterator
        assert ext.sources == ['file1', 'file2']
        ext = Extension('name', [pathlib.Path('file1'), 'file2'])  # mixed types
        assert ext.sources == ['file1', 'file2']

        # others arguments have defaults
        for attr in (
            'include_dirs',
            'define_macros',
            'undef_macros',
            'library_dirs',
            'libraries',
            'runtime_library_dirs',
            'extra_objects',
            'extra_compile_args',
            'extra_link_args',
            'export_symbols',
            'swig_opts',
            'depends',
        ):
            assert getattr(ext, attr) == []

        assert ext.language is None
        assert ext.optional is False

        # if there are unknown keyword options, warn about them
        msg = re.escape("unknown `Extension` options: 'chic'")
        with pytest.warns(UserWarning, match=msg) as w:
            warnings.simplefilter('always')
            ext = Extension('name', ['file1', 'file2'], chic=True)

        assert len(w) == 1


def test_can_be_extended_by_setuptools() -> None:
    # Emulate how it could be extended in setuptools

    @dataclass(init=True if TYPE_CHECKING else False)  # type: ignore[literal-required]
    class setuptools_Extension(Extension):
        py_limited_api: bool = False
        _full_name: str = field(init=False, repr=False)

        if not TYPE_CHECKING:
            # Custom __init__ is only needed for backwards compatibility
            # (to ignore arbitrary keywords)

            def __init__(self, *args, py_limited_api=False, **kwargs):
                self.py_limited_api = py_limited_api
                super().__init__(*args, **kwargs)

    ext1 = setuptools_Extension("name", ["hello.c"], py_limited_api=True)
    assert ext1.py_limited_api is True
    assert ext1.define_macros == []

    msg = re.escape("unknown `Extension` options: 'world'")
    with pytest.warns(UserWarning, match=msg):
        ext2 = setuptools_Extension("name", ["hello.c"], world=True)  # type: ignore[call-arg]

    assert "world" not in ext2.__dict__
    assert ext2.py_limited_api is False

    # Without __init__ customization the following warning would be an error:
    msg = re.escape("unknown `Extension` options: '_full_name'")
    with pytest.warns(UserWarning, match=msg):
        ext3 = setuptools_Extension("name", ["hello.c"], _full_name="hello")  # type: ignore[call-arg]

    assert "_full_name" not in ext3.__dict__
    ext3._full_name = "hello world"  # can still be set in build_ext
    assert ext3._full_name == "hello world"
