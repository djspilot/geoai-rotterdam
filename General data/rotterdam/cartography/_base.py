"""Rotterdam cartographic conventions: styling, scalebar, basemap, save.

Standard pipeline:

    fig, ax = point_map(...)        # or choropleth(...)
    finalize_map(fig, source=..., date=...)
    validate_map(fig, ax, data=...)
    save_map(fig, "naam")           # → output/maps/naam.png

`STYLE` (in vocab.py) is the single source of typography/colour defaults.
"""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd

from ..paths import MAPS_DIR
from ..vocab import ASSET_COLORS, RD_NEW, STYLE, nl_getal

# matplotlib's fysieke eenheid is de inch (dpi_scale_trans). We stellen de
# lay-out-marges echter in MILLIMETERS op (leesbaarder in NL-context) en rekenen op
# het gebruikspunt om: inches = mm * MM.
MM = 1.0 / 25.4                # inch per millimeter

# Corner elements (legend, north arrow, inside scale bar) sit at a fixed distance
# from the map edge: LEGEND_MARGIN[0] = horizontal inset in *axes fraction*;
# MARGIN_MM = vertical inset in *millimeters* (fixed physical size so it doesn't scale
# with the map's aspect ratio). MARGIN_IN is the same value in inches, afgeleid van de
# mm-bron, zodat de op inch gebaseerde plaatsingscode ongewijzigd blijft werken.
# LEGEND_MARGIN[1] is kept for backward-compat.
LEGEND_MARGIN = (0.01, 0.014)  # (x, y) axes fraction
MARGIN_MM = 3.3                # verticale hoekmarge in mm
MARGIN_IN = MARGIN_MM * MM     # zelfde marge in inch (matplotlib rekent in inch)

# Shared white box behind the legend / scale bar, so those frames always use the
# same colour and transparency. `alpha`/`facecolor`/`edgecolor` are applied to the
# legend (via ax.legend framealpha) and to the drawn scale-bar / size-legend boxes.
BOX_FACECOLOR = "white"
BOX_ALPHA = 0.85
BOX_EDGECOLOR = STYLE["separator_color"]
BOX_LINEWIDTH = 0.4


def _legend_anchor(ax, corner: str = "upper right") -> dict:
    """kwargs for `ax.legend` placing a legend `MARGIN_IN` inches (vertical) from
    the map edge, at `LEGEND_MARGIN[0]` (axes fraction) horizontally — so the
    margin is a fixed physical size regardless of the map's aspect ratio."""
    from matplotlib.transforms import blended_transform_factory, ScaledTranslation
    fig = ax.figure
    mx = LEGEND_MARGIN[0]
    top = "upper" in corner
    right = "right" in corner
    ytr = fig.dpi_scale_trans + ScaledTranslation(0, 1.0 if top else 0.0, ax.transAxes)
    btr = blended_transform_factory(ax.transAxes, ytr)
    return dict(loc=corner,
                bbox_to_anchor=((1 - mx) if right else mx, -MARGIN_IN if top else MARGIN_IN),
                bbox_transform=btr, borderaxespad=0)


def setup_headless_matplotlib() -> None:
    """Call before importing pyplot when running in a non-interactive env."""
    import matplotlib
    matplotlib.use("Agg")


def _available_fonts(families):
    """Keep only font families matplotlib can actually resolve.

    Prevents per-family `findfont: Font family '...' not found` warnings when
    e.g. Helvetica is unavailable (Windows). Always keeps at least one entry.
    """
    from matplotlib.font_manager import fontManager
    installed = {f.name for f in fontManager.ttflist}
    keep = [f for f in families if f in installed]
    return keep or ["DejaVu Sans"]


def _apply_rc():
    """Push the Rotterdam style into matplotlib rcParams (idempotent)."""
    import matplotlib as mpl
    mpl.rcParams["font.family"] = _available_fonts(STYLE["font_family"])
    mpl.rcParams["axes.titleweight"] = "bold"
    mpl.rcParams["axes.titlesize"] = STYLE["title_size"]
    mpl.rcParams["axes.edgecolor"] = STYLE["separator_color"]
    mpl.rcParams["axes.linewidth"] = 0.5
    mpl.rcParams["savefig.facecolor"] = STYLE["fig_bg"]
    mpl.rcParams["figure.facecolor"] = STYLE["fig_bg"]


def _nice_number(x: float) -> float:
    """Largest 1/2/5 x 10^k not exceeding x (>0). Used to pick a round scale length."""
    if x <= 0:
        return 1.0
    exp = math.floor(math.log10(x))
    base = 10.0 ** exp
    for m in (5, 2, 1):
        if m * base <= x:
            return m * base
    return base



__all__ = [
    "MM", "LEGEND_MARGIN", "MARGIN_MM", "MARGIN_IN",
    "BOX_FACECOLOR", "BOX_ALPHA", "BOX_EDGECOLOR", "BOX_LINEWIDTH",
    "STYLE", "ASSET_COLORS", "RD_NEW", "MAPS_DIR", "nl_getal",
    "setup_headless_matplotlib",
    "_legend_anchor", "_apply_rc", "_available_fonts", "_nice_number",
]
