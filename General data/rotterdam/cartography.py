"""Rotterdam cartographic conventions: styling, scalebar, basemap, save.

Standard pipeline:

    fig, ax = point_map(...)        # or choropleth(...)
    finalize_map(fig, source=..., date=...)
    validate_map(fig, ax, data=...)
    save_map(fig, "naam")           # → output/maps/naam.png

`STYLE` (in vocab.py) is the single source of typography/colour defaults.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from .paths import MAPS_DIR
from .vocab import ASSET_COLORS, RD_NEW, STYLE


def setup_headless_matplotlib() -> None:
    """Call before importing pyplot when running in a non-interactive env."""
    import matplotlib
    matplotlib.use("Agg")


def _apply_rc():
    """Push the Rotterdam style into matplotlib rcParams (idempotent)."""
    import matplotlib as mpl
    mpl.rcParams["font.family"] = STYLE["font_family"]
    mpl.rcParams["axes.titleweight"] = "bold"
    mpl.rcParams["axes.titlesize"] = STYLE["title_size"]
    mpl.rcParams["axes.edgecolor"] = STYLE["separator_color"]
    mpl.rcParams["axes.linewidth"] = 0.5
    mpl.rcParams["savefig.facecolor"] = STYLE["fig_bg"]
    mpl.rcParams["figure.facecolor"] = STYLE["fig_bg"]


def add_scalebar(ax, location: str = "lower left", total_m: int = 1000,
                 n_segments: int = 4) -> None:
    """Checkerboard scale bar: total length `total_m`, split in `n_segments`
    alternating black/white blocks with tick labels. Placed *below* the map
    (in axes-fraction coords) so it never overlaps the geometry. Assumes
    EPSG:28992 for the data axis.
    """
    from matplotlib.patches import Rectangle

    x0, x1 = ax.get_xlim()
    data_width = x1 - x0
    if data_width <= 0:
        return
    bar_frac = min(total_m / data_width, 0.4)
    seg_frac = bar_frac / n_segments

    x_start = 0.04
    y_bar = -0.045
    height = 0.012

    for i in range(n_segments):
        fc = "black" if i % 2 == 0 else "white"
        ax.add_patch(Rectangle(
            (x_start + i * seg_frac, y_bar), seg_frac, height,
            facecolor=fc, edgecolor="black", linewidth=0.8,
            transform=ax.transAxes, clip_on=False, zorder=10,
        ))

    seg_m = total_m / n_segments
    label_y = y_bar + height + 0.005
    for i in range(n_segments + 1):
        meters = int(i * seg_m)
        ax.text(x_start + i * seg_frac, label_y, f"{meters}",
                transform=ax.transAxes, ha="center", va="bottom",
                fontsize=8, color="#222222", clip_on=False, zorder=10)
    ax.text(x_start + bar_frac + 0.008, y_bar + height / 2, "m",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=8, color="#222222", clip_on=False, zorder=10)
    ax._rgeoai_scalebar = True


def add_north_arrow(ax, x: float = 0.05, y: float = 0.95) -> None:
    # Arrow points up (north): arrowhead at top (xy), tail below (xytext); "N" sits above the head.
    ax.annotate(
        "", xy=(x, y), xytext=(x, y - 0.05), xycoords="axes fraction",
        arrowprops=dict(arrowstyle="->", lw=1.5),
    )
    ax.text(
        x, y + 0.01, "N", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=12, fontweight="bold",
    )


def add_pdok_basemap(ax, layer: str = "grijs") -> None:
    """Add the PDOK BRT achtergrondkaart as a contextily basemap.

    Layer options: 'standaard', 'grijs', 'pastel', 'water'. Axis must be in EPSG:28992.
    """
    import contextily as cx
    url = (
        "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0?"
        f"layer={layer}&style=default&tilematrixset=EPSG:28992"
        "&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/png"
        "&TileMatrix={z}&TileCol={x}&TileRow={y}"
    )
    cx.add_basemap(ax, crs=f"EPSG:{RD_NEW}", source=url)


def style_map(ax, title: str, *, subtitle: str | None = None,
              scalebar: bool = True, north: bool = True) -> None:
    """Apply Rotterdam cartographic styling to one axes."""
    _apply_rc()
    ax.set_axis_off()
    ax.set_facecolor(STYLE["ax_bg"])

    ax.set_title(
        title, fontsize=STYLE["title_size"], fontweight=STYLE["title_weight"],
        color=STYLE["title_color"], loc="left", pad=14,
    )
    if subtitle:
        ax.text(
            0.0, 1.0, subtitle, transform=ax.transAxes,
            fontsize=STYLE["subtitle_size"], color=STYLE["subtitle_color"],
            weight=STYLE["subtitle_weight"], va="top",
        )
    if scalebar:
        add_scalebar(ax)
    if north:
        add_north_arrow(ax)


def finalize_map(
    fig, ax=None, *,
    source: str = "Obsurv via diensten.rotterdam.nl",
    date: str | None = None,
    author: str | None = None,
    suptitle: str | None = None,
    suptitle_subtitle: str | None = None,
    pad: float = 0.04,
) -> None:
    """Figure-level polish: footer with source, optional suptitle, clean margins.

    Call as last step before `save_map`.
    """
    from datetime import date as _date
    import matplotlib.lines as mlines
    _apply_rc()
    if date is None:
        date = _date.today().isoformat()

    fig.set_facecolor(STYLE["fig_bg"])

    if suptitle:
        fig.suptitle(suptitle, fontsize=18, fontweight="bold",
                     color=STYLE["title_color"], x=0.05, ha="left", y=0.98)
        if suptitle_subtitle:
            fig.text(0.05, 0.945, suptitle_subtitle,
                     fontsize=STYLE["subtitle_size"],
                     color=STYLE["subtitle_color"], ha="left")
        top = 0.90
    else:
        top = 0.94

    footer_parts = [f"Bron: {source}", f"Datum: {date}"]
    if author:
        footer_parts.append(author)
    fig.text(0.05, 0.02, "  ·  ".join(footer_parts),
             fontsize=STYLE["footer_size"], color=STYLE["footer_color"],
             ha="left")
    sep = mlines.Line2D([0.05, 0.95], [0.04, 0.04],
                        color=STYLE["separator_color"], lw=0.5,
                        transform=fig.transFigure, figure=fig)
    fig.lines.append(sep)

    fig.subplots_adjust(left=pad, right=1 - pad, top=top, bottom=0.06)


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

    if not (ax.get_title() or any(t.get_text() for t in fig.texts)):
        warns.append("Geen titel — voeg toe via style_map(ax, title=...).")

    has_legend = ax.get_legend() is not None
    has_colorbar = len(fig.axes) > 1
    if not (has_legend or has_colorbar):
        warns.append("Geen legenda of colorbar.")

    if not getattr(ax, "_rgeoai_scalebar", False):
        warns.append("Geen schaalstok — call add_scalebar(ax) of style_map(ax, ...).")

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

    leg = ax.legend(loc="upper right", frameon=True, facecolor="white",
                    edgecolor=STYLE["separator_color"], fontsize=9)
    if leg:
        leg.get_frame().set_linewidth(0.4)
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
            "title": legend_label or column,
            "loc": "lower right",
            "title_fontsize": 9,
            "fontsize": 8,
            "frameon": True,
            "facecolor": "white",
            "edgecolor": STYLE["separator_color"],
        },
    )
    style_map(ax, title, subtitle=subtitle)
    return fig, ax
