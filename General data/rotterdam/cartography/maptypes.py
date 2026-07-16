"""Kaarttypes + opslaan/valideren: point_map, choropleth, save_map, validate_map."""
from __future__ import annotations

import geopandas as gpd
from pathlib import Path

from ._base import *
from .basemaps import add_pdok_basemap
from .finalize import style_map

def save_map(fig, name: str, *, dpi: int = 150, fmt: str = "png",
             into: Path | None = None) -> Path:
    """Save figure to `output/maps/` (default) with a stable filename."""
    target_dir = into or MAPS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{name}.{fmt}"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=STYLE["fig_bg"])
    return path


def validate_map(
    fig, ax, *,
    data: gpd.GeoDataFrame | None = None,
    normalized: bool | None = None,
    n_classes: int | None = None,
    strict: bool = False,
) -> list[str]:
    """Check a finished map against the Rotterdam kartografische richtlijnen."""
    warns: list[str] = []

    _titles = [ax.get_title(loc=_l) for _l in ("center", "left", "right")]
    _sup = getattr(fig, "_suptitle", None)
    if _sup is not None and _sup.get_text().strip():
        _titles.append(_sup.get_text())
    if not any(s and s.strip() for s in _titles):
        warns.append("Geen titel — voeg toe via style_map(ax, title=...).")

    has_legend = ax.get_legend() is not None
    has_colorbar = len(fig.axes) > 1
    if not (has_legend or has_colorbar):
        warns.append("Geen legenda of colorbar.")

    if data is not None:
        if data.crs is None:
            warns.append("Data heeft geen CRS.")
        elif data.crs.to_epsg() != RD_NEW:
            warns.append(f"Data is in EPSG:{data.crs.to_epsg()}, niet EPSG:28992 (RD New).")

    if ax.axison:
        warns.append("Asassen staan aan — call ax.set_axis_off() of style_map(...).")

    if normalized is False:
        warns.append("Choropleet zonder normalisatie — deel door inwoners of oppervlak.")

    if n_classes is not None and n_classes > 9:
        warns.append(f"{n_classes} klassen is te veel (max 9, voorkeur 5).")

    # Bronvermelding in de footer (invariant 4 / 11)
    if not any(t.get_text().strip().lower().startswith("bron:") for t in fig.texts):
        warns.append("Geen bronvermelding — geef finalize_map(fig, source=...) mee.")

    # Titelhiërarchie (invariant 17): hoofdtitel vet, subtitel nooit vet
    import matplotlib.colors as _mc

    def _bold(t) -> bool:
        w = t.get_fontweight()
        return w in ("bold", "semibold", "demibold", "heavy", "black") or (
            isinstance(w, (int, float)) and w >= 600)

    _lt = getattr(ax, "_left_title", None)
    if _lt is not None and _lt.get_text().strip() and not _bold(_lt):
        warns.append("Hoofdtitel is niet vetgedrukt (invariant 17).")
    for _t in list(ax.texts) + list(fig.texts):
        try:
            _col = _mc.to_hex(_t.get_color()).lower()
        except Exception:
            continue
        if _t.get_text().strip() and _col == STYLE["subtitle_color"].lower() and _bold(_t):
            warns.append("Subtitel is vetgedrukt — subtitel mag nooit vet (invariant 17).")
            break

    # NL-getalnotatie (invariant 16): geen Engelse duizendtal-komma (bv. '20,028')
    import re as _re
    _texts = list(ax.texts) + list(fig.texts)
    if ax.get_legend() is not None:
        _texts += list(ax.get_legend().get_texts())
    _eng = _re.compile(r"\d,\d{3}(?!\d)")
    for _t in _texts:
        _s = _t.get_text()
        if _s and _eng.search(_s):
            warns.append(
                f"Engelse getalnotatie in label ('{_s.strip()}') — gebruik nl_getal() (invariant 16).")
            break

    if strict and warns:
        raise AssertionError("Kaart-validatie faalde:\n  - " + "\n  - ".join(warns))
    return warns


def point_map(
    points: gpd.GeoDataFrame,
    *,
    boundary: gpd.GeoDataFrame | None = None,
    title: str,
    subtitle: str | None = None,
    asset: str = "afvalbak",
    markersize: float = 3.0,
    alpha: float = 0.8,
    figsize: tuple[float, float] = (12, 12),
    basemap: bool = False,
    label: str | None = None,
):
    """Render a static point map. Returns (fig, ax)."""
    import matplotlib.pyplot as plt
    _apply_rc()
    fig, ax = plt.subplots(figsize=figsize)
    if boundary is not None:
        boundary.plot(ax=ax, facecolor=STYLE["polygon_fill"],
                      edgecolor=STYLE["boundary_color"],
                      linewidth=STYLE["boundary_width"])
    color = ASSET_COLORS.get(asset, "#d94841")
    points.plot(ax=ax, color=color, markersize=markersize, alpha=alpha,
                label=label or f"{asset} (n={len(points):,})")
    if basemap:
        add_pdok_basemap(ax)
    style_map(ax, title, subtitle=subtitle)

    leg = ax.legend(title="Legenda", frameon=True, facecolor=BOX_FACECOLOR,
                    edgecolor=BOX_EDGECOLOR, framealpha=BOX_ALPHA, fontsize=9,
                    **_legend_anchor(ax, "upper right"))
    if leg:
        leg.get_frame().set_linewidth(BOX_LINEWIDTH)
        leg.set_alignment("left")
        leg.get_title().set_fontweight("bold")
    return fig, ax


def choropleth(
    polygons: gpd.GeoDataFrame,
    column: str,
    *,
    title: str,
    subtitle: str | None = None,
    cmap: str = "YlOrRd",
    scheme: str = "quantiles",
    k: int = 5,
    figsize: tuple[float, float] = (12, 12),
    legend_label: str | None = None,
    integer_breaks: bool = True,
):
    """Standard choropleth per Rotterdam richtlijnen.

    Caller is responsible for normalising `column` (per 1000 inwoners, per km²).
    Plotting raw counts is a cartographic mistake.
    """
    import matplotlib.pyplot as plt
    import mapclassify
    _apply_rc()

    valid = polygons[polygons[column].notna()]
    if valid.empty:
        raise ValueError(f"Kolom '{column}' bevat alleen NaN — niets te plotten.")

    fig, ax = plt.subplots(figsize=figsize)

    classifier_name = {"quantiles": "Quantiles", "natural_breaks": "NaturalBreaks",
                       "equal_interval": "EqualInterval"}.get(scheme, "Quantiles")
    cls = mapclassify.classify(valid[column].to_numpy(),
                               scheme=classifier_name,
                               k=min(k, valid[column].nunique()))
    bins = list(cls.bins)
    if integer_breaks:
        bins = [round(b) for b in bins]

    polygons.plot(
        ax=ax, column=column, cmap=cmap,
        scheme="user_defined", classification_kwds={"bins": bins},
        legend=True, edgecolor=STYLE["boundary_color"],
        linewidth=STYLE["boundary_width"],
        missing_kwds={"color": "#eeeeee", "label": "Waarde onbekend",
                      "edgecolor": STYLE["boundary_color"], "linewidth": 0.3},
        legend_kwds={
            "title": "Legenda",   # altijd 'Legenda' (legend_label wordt genegeerd)
            "title_fontsize": 9,
            "fontsize": 8,
            "frameon": True,
            "facecolor": "white",
            "edgecolor": STYLE["separator_color"],
            **_legend_anchor(ax, "lower right"),
        },
    )
    leg = ax.get_legend()
    if leg is not None:
        leg.set_alignment("left")
        leg.get_title().set_fontweight("bold")
    style_map(ax, title, subtitle=subtitle)
    return fig, ax
