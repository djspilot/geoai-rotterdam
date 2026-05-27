"""Back-compat shim — the canonical Rotterdam GeoAI library lives in the project.

Real source: /Users/ds/Werk/GEOAI test/General data/rotterdam/

Old scripts that did:

    sys.path.insert(0, "/Users/ds/.claude/skills/rotterdam-geoai")
    from helpers import load_layer, point_map, ...

still work because this module re-exports the package's public API.

New scripts should import directly from the project package:

    sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")
    from rotterdam import load_layer, point_map, ...
"""

from __future__ import annotations

import sys

_PKG_PARENT = "/Users/ds/Werk/GEOAI test/General data"
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from rotterdam import *  # noqa: F401,F403,E402
from rotterdam import __all__  # noqa: E402
