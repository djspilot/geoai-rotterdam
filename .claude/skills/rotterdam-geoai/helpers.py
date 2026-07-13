"""Back-compat shim — the canonical Rotterdam GeoAI library lives in the project.

Real source: <project-root>/General data/rotterdam/

Old scripts that did:

    sys.path.insert(0, r"<project-root>/.claude/skills/rotterdam-geoai")
    from helpers import load_layer, point_map, ...

still work because this module re-exports the package's public API.

New scripts should import directly from the project package:

    sys.path.insert(0, r"<project-root>/General data")
    from rotterdam import load_layer, point_map, ...
"""

from __future__ import annotations

import sys
from pathlib import Path

# Derive the project root from this file's location instead of hardcoding it:
# helpers.py lives at <root>/.claude/skills/rotterdam-geoai/helpers.py
_PKG_PARENT = str(Path(__file__).resolve().parents[3] / "General data")
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from rotterdam import *  # noqa: F401,F403,E402
from rotterdam import __all__  # noqa: E402
