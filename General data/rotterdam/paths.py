"""Project paths. Single source of truth — never recompute `parents[N]` in scripts."""

from __future__ import annotations

from pathlib import Path

# Derived from this file's location so the project is portable across machines:
# paths.py → rotterdam/ → "General data"/ → PROJECT_ROOT
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERAL_DATA = PROJECT_ROOT / "General data"
DATA = GENERAL_DATA / "Data"
OUTPUT = PROJECT_ROOT / "output"
MAPS_DIR = OUTPUT / "maps"
DATA_OUT = OUTPUT / "data"
REPORTS_DIR = OUTPUT / "reports"
SCRIPTS_DIR = OUTPUT / "scripts"
CACHE = PROJECT_ROOT / "cache"

# Back-compat alias (helpers.py exposed `OUT` pointing at PROJECT_ROOT/output).
OUT = OUTPUT
