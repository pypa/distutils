import platform
import sys

collect_ignore = []


if "gcc" in sys.version.lower() or platform.system() != 'Windows':
    collect_ignore.extend([
        'distutils/command/bdist_msi.py',
        'distutils/msvc9compiler.py',
    ])
