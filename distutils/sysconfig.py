"""Provide access to Python's configuration information.  The specific
configuration variables available depend heavily on the platform and
configuration.  The values may be retrieved using
get_config_var(name), and the list of variables is available via
get_config_vars().keys().  Additional convenience functions are also
available.

Written by:   Fred L. Drake, Jr.
Email:        <fdrake@acm.org>
"""

import _imp
import os
import re
import sys
import sysconfig

from .errors import DistutilsPlatformError

IS_PYPY = '__pypy__' in sys.builtin_module_names

# These are needed in a couple of spots, so just compute them once.
PREFIX = os.path.normpath(sys.prefix)
EXEC_PREFIX = os.path.normpath(sys.exec_prefix)
BASE_PREFIX = os.path.normpath(sys.base_prefix)
BASE_EXEC_PREFIX = os.path.normpath(sys.base_exec_prefix)

# Path to the base directory of the project. On Windows the binary may
# live in project/PCbuild/win32 or project/PCbuild/amd64.
# set for cross builds
if "_PYTHON_PROJECT_BASE" in os.environ:
    project_base = os.path.abspath(os.environ["_PYTHON_PROJECT_BASE"])
else:
    if sys.executable:
        project_base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # sys.executable can be empty if argv[0] has been changed and Python is
        # unable to retrieve the real program name
        project_base = os.getcwd()


# python_build: (Boolean) if true, we're either building Python or
# building an extension with an un-installed Python, so we use
# different (hard-wired) directories.
def _is_python_source_dir(d):
    for fn in ("Setup", "Setup.local"):
        if os.path.isfile(os.path.join(d, "Modules", fn)):
            return True
    return False

_sys_home = getattr(sys, '_home', None)

if os.name == 'nt':
    def _fix_pcbuild(d):
        if d and os.path.normcase(d).startswith(
                os.path.normcase(os.path.join(PREFIX, "PCbuild"))):
            return PREFIX
        return d
    project_base = _fix_pcbuild(project_base)
    _sys_home = _fix_pcbuild(_sys_home)

def _python_build():
    if _sys_home:
        return _is_python_source_dir(_sys_home)
    return _is_python_source_dir(project_base)

python_build = _python_build()


# Calculate the build qualifier flags if they are defined.  Adding the flags
# to the include and lib directories only makes sense for an installation, not
# an in-source build.
build_flags = ''
try:
    if not python_build:
        build_flags = sys.abiflags
except AttributeError:
    # It's not a configure-based build, so the sys module doesn't have
    # this attribute, which is fine.
    pass

def get_python_version():
    """Return a string containing the major and minor Python version,
    leaving off the patchlevel.  Sample return values could be '1.5'
    or '2.2'.
    """
    return '%d.%d' % sys.version_info[:2]


def get_python_inc(plat_specific=0, prefix=None):
    """Return the directory containing installed Python header files.

    If 'plat_specific' is false (the default), this is the path to the
    non-platform-specific header files, i.e. Python.h and so on;
    otherwise, this is the path to platform-specific header files
    (namely pyconfig.h).

    If 'prefix' is supplied, use it instead of sys.base_prefix or
    sys.base_exec_prefix -- i.e., ignore 'plat_specific'.
    """
    if prefix is None:
        prefix = plat_specific and BASE_EXEC_PREFIX or BASE_PREFIX
    if os.name == "posix":
        if IS_PYPY and sys.version_info < (3, 8):
            return os.path.join(prefix, 'include')
        if python_build:
            # Assume the executable is in the build directory.  The
            # pyconfig.h file should be in the same directory.  Since
            # the build directory may not be the source directory, we
            # must use "srcdir" from the makefile to find the "Include"
            # directory.
            if plat_specific:
                return _sys_home or project_base
            else:
                incdir = os.path.join(get_config_var('srcdir'), 'Include')
                return os.path.normpath(incdir)
        implementation = 'pypy' if IS_PYPY else 'python'
        python_dir = implementation + get_python_version() + build_flags
        return os.path.join(prefix, "include", python_dir)
    elif os.name == "nt":
        if python_build:
            # Include both the include and PC dir to ensure we can find
            # pyconfig.h
            return (os.path.join(prefix, "include") + os.path.pathsep +
                    os.path.join(prefix, "PC"))
        return os.path.join(prefix, "include")
    else:
        raise DistutilsPlatformError(
            "I don't know where Python installs its C header files "
            "on platform '%s'" % os.name)


def get_python_lib(plat_specific=0, standard_lib=0, prefix=None):
    """Return the directory containing the Python library (standard or
    site additions).

    If 'plat_specific' is true, return the directory containing
    platform-specific modules, i.e. any module from a non-pure-Python
    module distribution; otherwise, return the platform-shared library
    directory.  If 'standard_lib' is true, return the directory
    containing standard Python library modules; otherwise, return the
    directory for site-specific modules.

    If 'prefix' is supplied, use it instead of sys.base_prefix or
    sys.base_exec_prefix -- i.e., ignore 'plat_specific'.
    """

    if IS_PYPY and sys.version_info < (3, 8):
        # PyPy-specific schema
        if prefix is None:
            prefix = PREFIX
        if standard_lib:
            return os.path.join(prefix, "lib-python", sys.version[0])
        return os.path.join(prefix, 'site-packages')

    if prefix is None:
        if standard_lib:
            prefix = plat_specific and BASE_EXEC_PREFIX or BASE_PREFIX
        else:
            prefix = plat_specific and EXEC_PREFIX or PREFIX

    if os.name == "posix":
        if plat_specific or standard_lib:
            # Platform-specific modules (any module from a non-pure-Python
            # module distribution) or standard Python library modules.
            libdir = getattr(sys, "platlibdir", "lib")
        else:
            # Pure Python
            libdir = "lib"
        implementation = 'pypy' if IS_PYPY else 'python'
        libpython = os.path.join(prefix, libdir,
                                 implementation + get_python_version())
        if standard_lib:
            return libpython
        else:
            return os.path.join(libpython, "site-packages")
    elif os.name == "nt":
        if standard_lib:
            return os.path.join(prefix, "Lib")
        else:
            return os.path.join(prefix, "Lib", "site-packages")
    else:
        raise DistutilsPlatformError(
            "I don't know where Python installs its library "
            "on platform '%s'" % os.name)



def customize_compiler(compiler):
    """Do any platform-specific customization of a CCompiler instance.

    Mainly needed on Unix, so we can plug in the information that
    varies across Unices and is stored in Python's Makefile.
    """
    if compiler.compiler_type == "unix":
        if sys.platform == "darwin":
            # Perform first-time customization of compiler-related
            # config vars on OS X now that we know we need a compiler.
            # This is primarily to support Pythons from binary
            # installers.  The kind and paths to build tools on
            # the user system may vary significantly from the system
            # that Python itself was built on.  Also the user OS
            # version and build tools may not support the same set
            # of CPU architectures for universal builds.
            global _config_vars
            # Use get_config_var() to ensure _config_vars is initialized.
            if not get_config_var('CUSTOMIZED_OSX_COMPILER'):
                import _osx_support
                _osx_support.customize_compiler(_config_vars)
                _config_vars['CUSTOMIZED_OSX_COMPILER'] = 'True'

        (cc, cxx, cflags, ccshared, ldshared, shlib_suffix, ar, ar_flags) = \
            get_config_vars('CC', 'CXX', 'CFLAGS',
                            'CCSHARED', 'LDSHARED', 'SHLIB_SUFFIX', 'AR', 'ARFLAGS')

        if 'CC' in os.environ:
            newcc = os.environ['CC']
            if('LDSHARED' not in os.environ
                    and ldshared.startswith(cc)):
                # If CC is overridden, use that as the default
                #       command for LDSHARED as well
                ldshared = newcc + ldshared[len(cc):]
            cc = newcc
        if 'CXX' in os.environ:
            cxx = os.environ['CXX']
        if 'LDSHARED' in os.environ:
            ldshared = os.environ['LDSHARED']
        if 'CPP' in os.environ:
            cpp = os.environ['CPP']
        else:
            cpp = cc + " -E"           # not always
        if 'LDFLAGS' in os.environ:
            ldshared = ldshared + ' ' + os.environ['LDFLAGS']
        if 'CFLAGS' in os.environ:
            cflags = cflags + ' ' + os.environ['CFLAGS']
            ldshared = ldshared + ' ' + os.environ['CFLAGS']
        if 'CPPFLAGS' in os.environ:
            cpp = cpp + ' ' + os.environ['CPPFLAGS']
            cflags = cflags + ' ' + os.environ['CPPFLAGS']
            ldshared = ldshared + ' ' + os.environ['CPPFLAGS']
        if 'AR' in os.environ:
            ar = os.environ['AR']
        if 'ARFLAGS' in os.environ:
            archiver = ar + ' ' + os.environ['ARFLAGS']
        else:
            archiver = ar + ' ' + ar_flags

        cc_cmd = cc + ' ' + cflags
        compiler.set_executables(
            preprocessor=cpp,
            compiler=cc_cmd,
            compiler_so=cc_cmd + ' ' + ccshared,
            compiler_cxx=cxx,
            linker_so=ldshared,
            linker_exe=cc,
            archiver=archiver)

        if 'RANLIB' in os.environ and compiler.executables.get('ranlib', None):
            compiler.set_executables(ranlib=os.environ['RANLIB'])

        compiler.shared_lib_extension = shlib_suffix


def get_config_h_filename():
    """Return full pathname of installed pyconfig.h file."""
    if python_build:
        if os.name == "nt":
            inc_dir = os.path.join(_sys_home or project_base, "PC")
        else:
            inc_dir = _sys_home or project_base
    else:
        inc_dir = get_python_inc(plat_specific=1)

    return os.path.join(inc_dir, 'pyconfig.h')


get_config_vars = sysconfig.get_config_vars
get_config_var = sysconfig.get_config_var
