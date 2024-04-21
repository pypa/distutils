"""distutils.spawn

Provides the 'spawn()' function, a front-end to various platform-
specific functions for launching another program in a sub-process.
Also provides the 'find_executable()' to search the path for a given
executable name.
"""

from __future__ import annotations

import os
import pathlib
import platform
import subprocess
import sys

from typing import Iterable

from ._log import log
from .debug import DEBUG
from .errors import DistutilsExecError


def spawn(cmd, search_path=1, verbose=0, dry_run=0, env=None):  # noqa: C901
    """Run another program, specified as a command list 'cmd', in a new process.

    'cmd' is just the argument list for the new process, ie.
    cmd[0] is the program to run and cmd[1:] are the rest of its arguments.
    There is no way to run a program with a name different from that of its
    executable.

    If 'search_path' is true (the default), the system's executable
    search path will be used to find the program; otherwise, cmd[0]
    must be the exact path to the executable.  If 'dry_run' is true,
    the command will not actually be run.

    Raise DistutilsExecError if running the program fails in any way; just
    return on success.
    """
    # cmd is documented as a list, but just in case some code passes a tuple
    # in, protect our %-formatting code against horrible death
    cmd = list(cmd)

    log.info(subprocess.list2cmdline(cmd))
    if dry_run:
        return

    if search_path:
        executable = find_executable(cmd[0])
        if executable is not None:
            cmd[0] = executable

    env = env if env is not None else dict(os.environ)

    if sys.platform == 'darwin':
        from distutils.util import MACOSX_VERSION_VAR, get_macosx_target_ver

        macosx_target_ver = get_macosx_target_ver()
        if macosx_target_ver:
            env[MACOSX_VERSION_VAR] = macosx_target_ver

    try:
        proc = subprocess.Popen(cmd, env=env)
        proc.wait()
        exitcode = proc.returncode
    except OSError as exc:
        if not DEBUG:
            cmd = cmd[0]
        raise DistutilsExecError(f"command {cmd!r} failed: {exc.args[-1]}") from exc

    if exitcode:
        if not DEBUG:
            cmd = cmd[0]
        raise DistutilsExecError(f"command {cmd!r} failed with exit code {exitcode}")


def _executable_candidates(executable: pathlib.Path):
    """
    Given an executable, yields common executable variants.
    """
    yield executable
    if platform.system() != 'Windows':
        return
    exts = os.environ.get('PATHEXT').split(os.pathsep)
    unique = (ext for ext in exts if executable.suffix.casefold() != ext.casefold())
    yield from map(executable.with_suffix, unique)


def _split_path(path: str | None) -> Iterable[str]:
    """
    Given a PATH, iterate over items of that path.

    >>> list(_split_path(os.pathsep.join(['foo', 'bar'])))
    ['foo', 'bar']

    An empty value should return no items.

    >>> list(_split_path(''))
    []

    A value of None also is empty.

    >>> list(_split_path(None))
    []

    A simply string will be the sole item.

    >>> list(_split_path('foo'))
    ['foo']

    A single separator should return a single empty string,
    representing the current directory:

    >>> list(_split_path(os.pathsep))
    ['']

    Similarly, an empty section should include the current directory:

    >>> list(_split_path(os.pathsep + 'foo'))
    ['', 'foo']
    """
    unique = dict.fromkeys
    return unique(path.split(os.path.pathsep)) if path else ()


def _resolve_path(path: str | None) -> str | None:
    """
    Resolve a path from a specified value, or from environmental state.
    """
    if path is not None:
        return path

    env = os.environ.get('PATH', None)
    # bpo-35755: Don't fall through if PATH is the empty string
    if env is not None:
        return env

    try:
        return os.confstr("CS_PATH")
    except (AttributeError, ValueError):
        # os.confstr() or CS_PATH is not available
        return os.defpath


def _search_paths(path):
    return map(pathlib.Path, _split_path(_resolve_path(path)))


def find_executable(executable, path=None):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or None if not found.
    """
    if os.path.isfile(executable):
        return executable

    found = (
        os.fspath(exe)
        for p in _search_paths(path)
        for exe in filter(pathlib.Path.is_file, _executable_candidates(p / executable))
    )
    return next(found, None)
