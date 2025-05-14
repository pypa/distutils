from __future__ import annotations

import sys
from types import ModuleType

grp: ModuleType | None = None
pwd: ModuleType | None = None
try:
    import grp
    import pwd
except ImportError:
    pass

import pytest

UNIX_ID_SUPPORT = grp and pwd
UID_0_SUPPORT = UNIX_ID_SUPPORT and sys.platform != "cygwin"

require_unix_id = pytest.mark.skipif(
    not UNIX_ID_SUPPORT, reason="Requires grp and pwd support"
)
require_uid_0 = pytest.mark.skipif(not UID_0_SUPPORT, reason="Requires UID 0 support")
