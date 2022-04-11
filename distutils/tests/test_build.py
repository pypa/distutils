"""Tests for distutils.command.build."""
import unittest
import os
import sys
from sysconfig import get_config_var, get_config_vars
from test.support import run_unittest

from distutils.command.build import build
from distutils.tests import support
from sysconfig import get_platform

class BuildTestCase(support.TempdirManager,
                    support.LoggingSilencer,
                    unittest.TestCase):

    def test_finalize_options(self):
        pkg_dir, dist = self.create_dist()
        cmd = build(dist)
        cmd.finalize_options()

        # if not specified, plat_name gets the current platform
        self.assertEqual(cmd.plat_name, get_platform())

        # build_purelib is build + lib
        wanted = os.path.join(cmd.build_base, 'lib')
        self.assertEqual(cmd.build_purelib, wanted)

        # build_platlib is 'build/lib.platform-x.x[-pydebug]'
        # examples:
        #   build/lib.macosx-10.3-i386-2.7
        plat_spec = '.%s-%s' % (cmd.plat_name, get_config_var("VERSION"))
        if hasattr(sys, 'gettotalrefcount'):
            self.assertTrue(cmd.build_platlib.endswith('-pydebug'))
            plat_spec += '-pydebug'
        wanted = os.path.join(cmd.build_base, 'lib' + plat_spec)
        self.assertEqual(cmd.build_platlib, wanted)

        # by default, build_lib = build_purelib
        self.assertEqual(cmd.build_lib, cmd.build_purelib)

        # build_temp is build/temp.<plat>
        wanted = os.path.join(cmd.build_base, 'temp' + plat_spec)
        self.assertEqual(cmd.build_temp, wanted)

        # build_scripts is build/scripts-x.x
        wanted = os.path.join(cmd.build_base,
                              'scripts-%d.%d' % sys.version_info[:2])
        self.assertEqual(cmd.build_scripts, wanted)

        # executable is os.path.normpath(sys.executable)
        self.assertEqual(cmd.executable, os.path.normpath(sys.executable))

    def test_custom_version(self):
        # Test to make sure that custom VERSION's make it into the paths

        config_vars = get_config_vars()
        orig_version = config_vars["VERSION"]

        # There is not an official API to modify sysconfig variables,
        # but modifying the config dict works.
        new_version = config_vars["VERSION"] = "customversion"
        self.assertEqual(get_config_var("VERSION"), new_version)

        try:
            pkg_dir, dist = self.create_dist()
            cmd = build(dist)
            cmd.finalize_options()

            wanted = os.path.join(cmd.build_base, f'lib.{cmd.plat_name}-customversion')
            assert cmd.build_platlib.startswith(wanted)
            assert cmd.build_platlib == wanted or cmd.build_platlib.endswith('-pydebug')
        finally:
            config_vars["VERSION"] = orig_version

def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(BuildTestCase)

if __name__ == "__main__":
    run_unittest(test_suite())
