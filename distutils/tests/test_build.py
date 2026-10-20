"""Tests for distutils.command.build."""

import os
import sys
from distutils.command.build import build
from distutils.extension import Extension
from distutils.tests import support
from sysconfig import get_config_var, get_config_vars, get_platform

import pytest


class TestBuild(support.TempdirManager):
    def test_finalize_options(self):
        _pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        # if not specified, plat_name gets the current platform
        assert cmd.plat_name == get_platform()

        # build_purelib is build + lib
        wanted = os.path.join(cmd.build_base, 'lib')
        assert cmd.build_purelib == wanted

        # build_platlib is 'build/lib.platform-soabi[-pydebug]'
        soabi = get_config_var('SOABI')
        plat_spec = f'.{cmd.plat_name}-{soabi or sys.implementation.cache_tag}'
        if not soabi and get_config_var('Py_GIL_DISABLED'):
            plat_spec += 't'
        if hasattr(sys, 'gettotalrefcount'):
            assert cmd.build_platlib.endswith('-pydebug')
            plat_spec += '-pydebug'
        wanted = os.path.join(cmd.build_base, 'lib' + plat_spec)
        assert cmd.build_platlib == wanted

        # by default, build_lib = build_purelib
        assert cmd.build_lib == cmd.build_purelib

        # build_temp is build/temp.<plat>
        wanted = os.path.join(cmd.build_base, 'temp' + plat_spec)
        assert cmd.build_temp == wanted

        # build_scripts is build/scripts-x.x
        wanted = os.path.join(
            cmd.build_base, f'scripts-{sys.version_info.major}.{sys.version_info.minor}'
        )
        assert cmd.build_scripts == wanted

        # executable is os.path.normpath(sys.executable)
        assert cmd.executable == os.path.normpath(sys.executable)

    @pytest.mark.parametrize(
        ('soabi', 'gil_disabled', 'debug'),
        [
            ('cpython-313-aarch64-linux-gnu', 0, 0),
            ('cpython-314-aarch64-linux-gnu', 0, 0),
            ('cpython-314d-aarch64-linux-gnu', 0, 1),
            ('cpython-314t-aarch64-linux-gnu', 1, 0),
            ('cpython-314td-aarch64-linux-gnu', 1, 1),
            ('cp314-win_arm64', 0, 0),
            ('pypy311-pp80-aarch64-linux-gnu', 0, 0),
            ('graalpy231-310-native-aarch64-linux', 0, 0),
        ],
    )
    def test_target_abi(self, monkeypatch, soabi, gil_disabled, debug):
        monkeypatch.setitem(get_config_vars(), 'SOABI', soabi)
        monkeypatch.setitem(get_config_vars(), 'Py_GIL_DISABLED', gil_disabled)
        monkeypatch.setitem(get_config_vars(), 'Py_DEBUG', debug)
        _pkg_dir, dist = self.create_dist(ext_modules=[Extension('foo', ['foo.c'])])
        cmd = build(dist)
        cmd.finalize_options()

        tag = soabi + ('-pydebug' if debug else '')
        assert cmd.build_platlib == os.path.join('build', f'lib.{cmd.plat_name}-{tag}')
        assert cmd.build_temp == os.path.join('build', f'temp.{cmd.plat_name}-{tag}')
        assert cmd.build_lib == cmd.build_platlib

    @pytest.mark.parametrize('debug', [0, 1])
    @pytest.mark.parametrize('native_debug', [False, True])
    def test_target_debug(self, monkeypatch, debug, native_debug):
        monkeypatch.setitem(get_config_vars(), 'SOABI', 'cp314-win_arm64')
        monkeypatch.setitem(get_config_vars(), 'Py_DEBUG', debug)
        if native_debug:
            monkeypatch.setattr(sys, 'gettotalrefcount', lambda: 0, raising=False)
        else:
            monkeypatch.delattr(sys, 'gettotalrefcount', raising=False)
        _pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        tag = 'cp314-win_arm64' + ('-pydebug' if debug else '')
        assert cmd.build_platlib == os.path.join('build', f'lib.{cmd.plat_name}-{tag}')
        assert cmd.build_temp == os.path.join('build', f'temp.{cmd.plat_name}-{tag}')

    @pytest.mark.parametrize(
        ('version', 'expected'),
        [('3.13', '3.13'), ('3.15', '3.15'), ('315', '3.15'), (315, '3.15')],
    )
    def test_target_version(self, monkeypatch, version, expected):
        monkeypatch.setitem(get_config_vars(), 'VERSION', version)
        _pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        assert cmd.build_scripts == os.path.join('build', f'scripts-{expected}')

    @pytest.mark.parametrize('version', [None, '', 'invalid'])
    def test_missing_version(self, monkeypatch, version):
        monkeypatch.setitem(get_config_vars(), 'VERSION', version)
        _pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        expected = f'{sys.version_info.major}.{sys.version_info.minor}'
        assert cmd.build_scripts == os.path.join('build', f'scripts-{expected}')

    @pytest.mark.parametrize('debug', [None, 0, 1])
    @pytest.mark.parametrize('native_debug', [False, True])
    @pytest.mark.parametrize('gil_disabled', [0, 1])
    def test_missing_soabi(self, monkeypatch, debug, native_debug, gil_disabled):
        monkeypatch.setitem(get_config_vars(), 'SOABI', None)
        monkeypatch.setitem(get_config_vars(), 'Py_DEBUG', debug)
        monkeypatch.setitem(get_config_vars(), 'Py_GIL_DISABLED', gil_disabled)
        if native_debug:
            monkeypatch.setattr(sys, 'gettotalrefcount', lambda: 0, raising=False)
        else:
            monkeypatch.delattr(sys, 'gettotalrefcount', raising=False)
        _pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        tag = str(sys.implementation.cache_tag)
        if gil_disabled:
            tag += 't'
        expected_debug = debug if debug is not None else native_debug
        if expected_debug:
            tag += '-pydebug'
        assert cmd.build_platlib == os.path.join('build', f'lib.{cmd.plat_name}-{tag}')
        assert cmd.build_temp == os.path.join('build', f'temp.{cmd.plat_name}-{tag}')

    def test_directory_overrides(self, monkeypatch):
        monkeypatch.setitem(get_config_vars(), 'SOABI', 'cpython-315-aarch64-linux-gnu')
        monkeypatch.setitem(get_config_vars(), 'VERSION', '3.15')
        _pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        directories = {
            'build_purelib': 'custom-purelib',
            'build_platlib': 'custom-platlib',
            'build_lib': 'custom-lib',
            'build_temp': 'custom-temp',
            'build_scripts': 'custom-scripts',
        }
        for name, value in directories.items():
            setattr(cmd, name, value)
        cmd.finalize_options()

        for name, value in directories.items():
            assert getattr(cmd, name) == value
