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

from .paths import MAPS_DIR
from .vocab import ASSET_COLORS, RD_NEW, STYLE, nl_getal

# Corner elements (legend, north arrow, inside scale bar) sit at a fixed distance
# from the map edge: LEGEND_MARGIN[0] = horizontal inset in *axes fraction*;
# MARGIN_IN = vertical inset in *inches* (fixed physical size so it doesn't scale
# with the map's aspect ratio). LEGEND_MARGIN[1] is kept for backward-compat.
LEGEND_MARGIN = (0.01, 0.014)  # (x, y) axes fraction
MARGIN_IN = 0.13               # vertical corner margin in inches

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


def add_scalebar(ax, location: str = "lower left", total_m: int | None = None,
                 n_segments: int = 5, *, inside: bool = False,
                 box: bool = False, variant: str = "B") -> None:
    """Scale bar with tick labels, assuming EPSG:28992 for the data axis. Twee
    varianten (zelfde lengte, labels, eenheid en plaatsing):

    - **"B"** (**default**): één enkele **lijn** met verticale streepjes bij elke
      segmentgrens.
    - **"A"**: geblokte balk — `n_segments` afwisselend zwart/witte blokken.

    By default the bar sits *below* the map (in the bottom margin) so it never
    overlaps the geometry. With `inside=True` it is drawn *on* the map in a bottom
    corner: `location="lower left"` (default) or `"lower right"` when the left is
    occupied (invariant 14). `box=False` (default) draws **no frame** — the labels
    get a subtle white halo so they stay readable on the basemap; `box=True` puts
    the bar on a semi-transparent white box instead.

    `total_m` defaults to an adaptive round length (~1/5 of the map width).
    The unit (m/km) is chosen from the segment length so tick labels are
    always whole numbers — km only when each segment is a whole number of km,
    otherwise metres. Wide extents like Rotterdam Zuid therefore get clean
    whole-km ticks without crowding.
    """
    from matplotlib.patches import Rectangle
    from matplotlib.lines import Line2D

    x0, x1 = ax.get_xlim()
    data_width = x1 - x0
    if data_width <= 0:
        return

    if total_m is None:
        # Aim for a bar ~20% of the map width, rounded to a nice segment length.
        seg_m = _nice_number((data_width * 0.20) / n_segments)
        total_m = seg_m * n_segments
    else:
        seg_m = total_m / n_segments

    bar_frac = min(total_m / data_width, 0.4)
    seg_frac = bar_frac / n_segments

    # x follows the map (axes fraction, so the bar length tracks the data width),
    # but y/heights are in *inches* (fig.dpi_scale_trans) so the bar keeps a fixed
    # physical height regardless of the map's aspect ratio (a tall portrait map
    # would otherwise stretch an axes/figure-fraction bar vertically).
    from matplotlib.transforms import blended_transform_factory, ScaledTranslation
    fig = ax.figure
    mx, my = LEGEND_MARGIN
    height, label_off = 0.06, 0.03            # inches

    if inside:
        # on the map, lower-left; y=0 at the bottom edge, MARGIN_IN keeps a fixed
        # vertical gap (inches). Boxless (default) sits at MARGIN_IN so it lines up
        # with the legend/north arrow margin; with a box it lifts a touch so the
        # frame has room below the bar.
        ytr = fig.dpi_scale_trans + ScaledTranslation(0, 0.0, ax.transAxes)
        tr = blended_transform_factory(ax.transAxes, ytr)
        x_start, y_bar = mx + 0.025, (MARGIN_IN + 0.10) if box else MARGIN_IN
    else:
        # below the map: anchored in the bottom margin (figure y=0.05), sized in inches
        ytr = fig.dpi_scale_trans + ScaledTranslation(0, 0.05, fig.transFigure)
        tr = blended_transform_factory(ax.transAxes, ytr)
        x_start, y_bar = 0.04, 0.0

    parts = []                         # artists to fit the inside box around
    if str(variant).upper() == "A":
        # variant A: geblokte balk — afwisselend zwart/witte blokken
        for i in range(n_segments):
            fc = "black" if i % 2 == 0 else "white"
            r = Rectangle((x_start + i * seg_frac, y_bar), seg_frac, height,
                          facecolor=fc, edgecolor="black", linewidth=0.8,
                          transform=tr, clip_on=False, zorder=10)
            ax.add_patch(r)
            parts.append(r)
    else:
        # variant B: één enkele lijn met verticale streepjes bij elke segmentgrens
        base = Line2D([x_start, x_start + bar_frac], [y_bar, y_bar],
                      transform=tr, color="black", linewidth=1.2,
                      clip_on=False, zorder=10)
        ax.add_line(base)
        parts.append(base)
        for i in range(n_segments + 1):
            xt = x_start + i * seg_frac
            tick = Line2D([xt, xt], [y_bar, y_bar + height],
                          transform=tr, color="black", linewidth=1.0,
                          clip_on=False, zorder=10)
            ax.add_line(tick)
            parts.append(tick)

    # Label in km only when the segment length is a whole number of km,
    # otherwise metres — so tick labels stay whole numbers and never turn
    # into halves (a 500 m segment shows "500 m", not "0.5 km").
    use_km = seg_m >= 1000 and seg_m % 1000 == 0
    div = 1000.0 if use_km else 1.0
    unit = "km" if use_km else "m"
    label_y = y_bar + height + label_off
    for i in range(n_segments + 1):
        val = i * seg_m / div
        parts.append(ax.text(x_start + i * seg_frac, label_y, f"{val:g}",
                     transform=tr, ha="center", va="bottom",
                     fontsize=8, color="#222222", clip_on=False, zorder=10))
    parts.append(ax.text(x_start + bar_frac + 0.008, y_bar + height / 2, unit,
                 transform=tr, ha="left", va="center",
                 fontsize=8, color="#222222", clip_on=False, zorder=10))
    ax._rgeoai_scalebar = True

    if inside:
        # Fit the white box snugly around the drawn bar + labels (measure their
        # union in display space, map back to the bar's blended transform).
        from matplotlib.text import Text
        from matplotlib.transforms import Bbox
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        union = Bbox.union([p.get_window_extent(rend) for p in parts])
        inv = tr.inverted()
        (bx0, by0) = inv.transform((union.x0, union.y0))
        (bx1, by1) = inv.transform((union.x1, union.y1))
        px, py = 0.008, 0.05           # padding: axes-fraction x, inch y
        # Align to LEGEND_MARGIN so the scale bar keeps the same horizontal margin
        # to the map edge as the north arrow / legend. With a box the frame edge is
        # aligned (content sits px inside); boxless the content itself is aligned,
        # so it sits flush at the margin. 'lower right' aligns the right edge to
        # (1 - mx); otherwise the left edge to mx (default).
        pad = px if box else 0.0
        dx = ((1 - mx) - (bx1 + pad)) if "right" in location else (mx - (bx0 - pad))
        if abs(dx) > 1e-6:
            for p in parts:
                if isinstance(p, Text):
                    tx, ty = p.get_position()
                    p.set_position((tx + dx, ty))
                elif isinstance(p, Line2D):        # variant B: lijn/streepjes
                    p.set_xdata([xx + dx for xx in p.get_xdata()])
                else:
                    p.set_x(p.get_x() + dx)
            bx0, bx1 = bx0 + dx, bx1 + dx
        if box:
            ax.add_patch(Rectangle(
                (bx0 - px, by0 - py), (bx1 - bx0) + 2 * px, (by1 - by0) + 2 * py,
                transform=tr, facecolor=BOX_FACECOLOR, alpha=BOX_ALPHA,
                edgecolor=BOX_EDGECOLOR, linewidth=BOX_LINEWIDTH, zorder=9,
                clip_on=False))
        else:
            # no frame: give the labels a subtle white halo so they stay readable
            # directly on the basemap
            import matplotlib.patheffects as pe
            halo = [pe.withStroke(linewidth=1.8, foreground="white")]
            for p in parts:
                if isinstance(p, Text):
                    p.set_path_effects(halo)
        # Reserve the footprint so place_legend never lands on the bar.
        _reserve_zone(ax, x0_frac=bx0 - px, x1_frac=bx1 + px,
                      edge_y="bottom", y0_in=0.0, y1_in=by1 + py)


def add_scale_ratio(ax, *, prefix: str = "1:", loc: str = "lower left") -> str:
    """Draw a numeric scale as a **1:x** ratio in a corner — a drop-in alternative
    to `add_scalebar`.

    The ratio is computed from the map's *physical* width on the figure (axes
    inches) and its ground width (EPSG:28992, metres), so call it **after** the
    final layout (`finalize_map` / `fit_figure_to_data` / `add_side_panel`). The
    number is rounded to two significant figures and formatted NL-style
    (`1:13.000`). `loc`: 'lower left'|'lower right'|'upper left'|'upper right'.
    Returns the ratio string.
    """
    import math
    fig = ax.figure
    fig.canvas.draw()
    x0, x1 = ax.get_xlim()
    ground_m = abs(x1 - x0)
    axes_w_in = ax.get_window_extent().width / fig.dpi
    if axes_w_in <= 0 or ground_m <= 0:
        return ""
    scale = ground_m / (axes_w_in * 0.0254)              # 1 : scale
    mag = 10 ** (math.floor(math.log10(scale)) - 1)      # two significant figures
    scale_r = int(round(scale / mag) * mag)
    text = prefix + format(scale_r, ",d").replace(",", ".")

    mx, my = LEGEND_MARGIN
    corners = {
        "lower left":  (mx, my, "left", "bottom"),
        "lower right": (1 - mx, my, "right", "bottom"),
        "upper left":  (mx, 1 - my, "left", "top"),
        "upper right": (1 - mx, 1 - my, "right", "top"),
    }
    px, py, ha, va = corners.get(loc, corners["lower left"])
    ax.text(px, py, text, transform=ax.transAxes, ha=ha, va=va,
            fontsize=8.5, color="#222222", zorder=12,
            bbox=dict(boxstyle="round,pad=0.35", facecolor=BOX_FACECOLOR,
                      alpha=BOX_ALPHA, edgecolor=BOX_EDGECOLOR,
                      linewidth=BOX_LINEWIDTH))
    return text


def add_north_arrow(ax, x: float | None = None, y: float | None = None, *,
                    corner: str = "upper left", variant: str = "B") -> None:
    """Triangular north arrow with 'N' above the apex, at the **top** of the map
    (invariant 13). Twee varianten (identiek qua vorm/plaatsing):

    - **"B"** (Noordpijl B, **default**): volledig zwart — beide helften zwart.
    - **"A"** (Noordpijl A): tweekleurig — linkerhelft zwart, rechterhelft wit.

    `corner`: 'upper left' (default) or 'upper right' — use the right corner when
    the left is occupied (e.g. by the legend). Drawn at a **fixed physical size**
    (inches, via `fig.dpi_scale_trans`) so it does not stretch on tall/portrait
    maps. `x`/`y` (axes fraction) override the anchor.
    """
    from matplotlib.patches import Polygon
    from matplotlib.transforms import ScaledTranslation

    fig = ax.figure
    mx = LEGEND_MARGIN[0]
    right = "right" in corner
    fx = ((1 - mx) if right else mx) if x is None else x
    fy = 1.0 if y is None else y          # top edge; fixed inch margin below it
    s = -1.0 if right else 1.0            # mirror x so a right arrow hugs the right edge
    # coordinates in inches, origin at the top anchor (y up; the arrow hangs
    # downward). MARGIN_IN keeps a fixed vertical gap below the top edge.
    tr = fig.dpi_scale_trans + ScaledTranslation(fx, fy, ax.transAxes)

    m = MARGIN_IN
    hw, th, ndf = 0.09, 0.27, 0.20        # half-width, triangle height, notch fraction (inches)
    gap = 0.15                            # gap between the 'N' and the apex (inches)
    apex = (s * hw, -m - gap)
    bl, br = (0.0, -m - gap - th), (s * 2 * hw, -m - gap - th)
    notch = (s * hw, -m - gap - th + ndf * th)

    dark = "#1a1a1a"
    right_fill = "white" if str(variant).upper() == "A" else dark   # "B" = volledig zwart
    ax.add_patch(Polygon([apex, bl, notch], closed=True, transform=tr,
                         facecolor=dark, edgecolor=dark, linewidth=0.8,
                         zorder=11, clip_on=False))
    ax.add_patch(Polygon([apex, notch, br], closed=True, transform=tr,
                         facecolor=right_fill, edgecolor=dark, linewidth=0.8,
                         zorder=11, clip_on=False))
    ax.text(s * hw, -m, "N", transform=tr, ha="center", va="top",
            fontsize=10, fontweight="bold", color="#1a1a1a", zorder=11)
    # Reserve the footprint so place_legend never lands on the arrow.
    if right:
        _reserve_zone(ax, x0_in_from_frac=(fx, 0.34), x1_frac=min(1.0, fx + 0.01),
                      edge_y="top", y0_in=0.0, y1_in=0.7)
    else:
        _reserve_zone(ax, x0_frac=max(0.0, fx - 0.01), x1_in_from_frac=(fx, 0.34),
                      edge_y="top", y0_in=0.0, y1_in=0.7)


def _reserve_zone(ax, **descriptor) -> None:
    """Register a furniture footprint (north arrow, scale bar) on the axes so
    `place_legend` avoids it. Boxes mix axes-fraction x with inch-from-edge y
    (furniture keeps a fixed physical size); resolved to axes fractions later."""
    ax._rdam_reserved = getattr(ax, "_rdam_reserved", []) + [descriptor]


def _reserved_boxes(ax, w_in: float, h_in: float):
    """Resolve registered furniture descriptors to axes-fraction AABBs
    (x0, x1, y0, y1) given the current axes size in inches."""
    boxes = []
    for d in getattr(ax, "_rdam_reserved", []):
        if "x0_in_from_frac" in d:          # anchor frac + inch extent to the left
            fx, ext_in = d["x0_in_from_frac"]
            x0 = fx - ext_in / w_in if w_in else 0.0
        else:
            x0 = d.get("x0_frac", 0.0)
        if "x1_in_from_frac" in d:          # anchor frac + inch extent to the right
            fx, ext_in = d["x1_in_from_frac"]
            x1 = fx + ext_in / w_in if w_in else 1.0
        else:
            x1 = d.get("x1_frac", 1.0)
        if d.get("edge_y") == "top":
            y0 = 1.0 - d.get("y1_in", 0.0) / h_in if h_in else 0.9
            y1 = 1.0 - d.get("y0_in", 0.0) / h_in if h_in else 1.0
        else:
            y0 = d.get("y0_in", 0.0) / h_in if h_in else 0.0
            y1 = d.get("y1_in", 0.0) / h_in if h_in else 0.1
        boxes.append((x0, x1, y0, y1))
    return boxes


def add_pdok_basemap(ax, layer: str = "grijs") -> None:
    """Add the PDOK BRT achtergrondkaart as a contextily basemap.

    Layer options: 'standaard', 'grijs', 'pastel', 'water', 'luchtfoto'.
    Axis must be in EPSG:28992.

    Uses contextily's built-in ``nlmaps`` provider — the same PDOK kaart served
    in EPSG:3857. contextily computes tile indices in Web Mercator, so a raw
    ``tilematrixset=EPSG:28992`` WMTS URL returns blank tiles; the nlmaps (3857)
    tiles are fetched and warped onto the RD axes instead. For the municipal
    Rotterdam basemap use `add_rotterdam_basemap`.
    """
    import contextily as cx
    try:
        source = cx.providers.nlmaps[layer]
    except KeyError:
        raise ValueError(
            f"Onbekende PDOK-laag {layer!r}; kies uit "
            f"{list(cx.providers.nlmaps.keys())}."
        )
    cx.add_basemap(ax, crs=f"EPSG:{RD_NEW}", source=source)


# Gemeente Rotterdam basemap services (ArcGIS MapServer, RD/EPSG:28992 cache).
ROTTERDAM_BASEMAPS = {
    "grijs": "https://diensten.rotterdam.nl/arcgis/rest/services/"
             "SB_BI/Basiskaart_BI_Grijs/MapServer",
    "kleur": "https://diensten.rotterdam.nl/arcgis/rest/services/"
             "SB_BI/Basiskaart_BI_Kleur/MapServer",
    "luchtfoto": "https://diensten.rotterdam.nl/arcgis/rest/services/"
                 "LUCHTFOTO/luchtfoto_actueel/MapServer",
}


def add_rotterdam_basemap(ax, layer: str = "grijs", *, max_tiles: int = 400,
                          target_res: float | None = None) -> None:
    """Add a Gemeente Rotterdam *Basiskaart* under the axes.

    These municipal basemaps are cached in **EPSG:28992 (RD)**, so contextily —
    which assumes Web Mercator tiling — cannot fetch them. This pulls the ArcGIS
    REST tiles directly and mosaics them onto the RD axes: no reprojection,
    exact alignment. (For the landelijke PDOK BRT kaart use `add_pdok_basemap`.)

    The axes must already be in EPSG:28992 with its final extent (call after
    plotting the data, before `add_scalebar`). `layer`: 'grijs', 'kleur' or
    'luchtfoto' (aerial imagery, up to ~5 cm/px).

    `target_res` overrides the automatic tile resolution (m/px); lower = sharper
    (useful for large/print exports). Bounded by `max_tiles`.
    """
    import io
    import json
    import urllib.request

    import numpy as np
    from PIL import Image

    from .arcgis import _ssl_context

    base = ROTTERDAM_BASEMAPS[layer]
    ctx = _ssl_context(verify=False)   # diensten.rotterdam.nl TLS chain trips verification

    def _get(u: str) -> bytes:
        with urllib.request.urlopen(u, context=ctx, timeout=120) as r:
            return r.read()

    ti = json.loads(_get(base + "?f=json"))["tileInfo"]
    X0, Y0 = ti["origin"]["x"], ti["origin"]["y"]
    tsz = ti["cols"]
    lods = sorted(ti["lods"], key=lambda l: l["resolution"])   # fine -> coarse

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    want = target_res if target_res else max(x1 - x0, y1 - y0) / 1800.0   # target m/px

    lod = lods[-1]
    for l in lods:
        span = l["resolution"] * tsz
        ntiles = (int((x1 - X0) // span) - int((x0 - X0) // span) + 1) * \
                 (int((Y0 - y0) // span) - int((Y0 - y1) // span) + 1)
        if l["resolution"] >= want or ntiles <= max_tiles:
            lod = l
            if l["resolution"] >= want and ntiles <= max_tiles:
                break
    lvl, res = lod["level"], lod["resolution"]
    span = res * tsz

    c0 = int((x0 - X0) // span); c1 = int((x1 - X0) // span)
    r0 = int((Y0 - y1) // span); r1 = int((Y0 - y0) // span)
    mosaic = Image.new("RGBA", ((c1 - c0 + 1) * tsz, (r1 - r0 + 1) * tsz), (255, 255, 255, 0))
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            try:
                tile = Image.open(io.BytesIO(_get(f"{base}/tile/{lvl}/{r}/{c}"))).convert("RGBA")
                mosaic.paste(tile, ((c - c0) * tsz, (r - r0) * tsz))
            except Exception:
                pass   # tile outside the cache — leave transparent

    ax.imshow(
        np.asarray(mosaic),
        extent=[X0 + c0 * span, X0 + (c1 + 1) * span,
                Y0 - (r1 + 1) * span, Y0 - r0 * span],
        origin="upper", zorder=0, interpolation="bilinear",
    )
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)


def style_map(ax, title: str, *, subtitle: str | None = None,
              scalebar: bool = False, north: "bool | str" = False,
              north_variant: str = "B", scalebar_variant: str = "B") -> None:
    """Apply Rotterdam cartographic styling to one axes.

    `north`: **default False** — een noordpijl is alleen nodig als het noorden niet
    recht naar boven wijst (gedraaide kaart) of bij een navigatiekaart (invariant
    13). Standaard noord-boven kaarten krijgen er dus géén. Zet `True` (pijl
    linksboven) of een hoek-string ('upper left'/'upper right') als een pijl wél
    nodig is — rechterhoek wanneer de linker bezet is.
    """
    _apply_rc()
    ax.set_axis_off()
    ax.set_facecolor(STYLE["ax_bg"])

    # Titel + subtitel staan ALTIJD boven de kaart, samen — nooit óver de kaart
    # (invariant "Titel en subtitel boven de kaart"). De subtitel komt net boven de
    # kaartrand (va="bottom", kleine fysieke marge) en de titel krijgt genoeg pad
    # om daar nog net boven te vallen.
    pad = 14
    if subtitle:
        from matplotlib.transforms import ScaledTranslation
        sub_gap_in = 3 / 72.0                     # subtitel-onderkant boven de kaartrand
        ax.text(
            0.0, 1.0, subtitle,
            transform=ax.transAxes
            + ScaledTranslation(0, sub_gap_in, ax.figure.dpi_scale_trans),
            ha="left", va="bottom",
            fontsize=STYLE["subtitle_size"], color=STYLE["subtitle_color"],
            weight=STYLE["subtitle_weight"],
        )
        pad = int(round(sub_gap_in * 72 + STYLE["subtitle_size"] + 8))  # titel boven de subtitel

    ax.set_title(
        title, fontsize=STYLE["title_size"], fontweight=STYLE["title_weight"],
        color=STYLE["title_color"], loc="left", pad=pad,
    )
    if scalebar:
        add_scalebar(ax, variant=scalebar_variant)
    if north:
        add_north_arrow(ax, corner=north if isinstance(north, str) else "upper left",
                        variant=north_variant)


def finalize_map(
    fig, ax=None, *,
    source: str = "Obsurv via diensten.rotterdam.nl",
    date: str | None = None,
    author: str | None = None,
    suptitle: str | None = None,
    suptitle_subtitle: str | None = None,
    pad: float = 0.04,
    tight_bottom: bool = False,
) -> None:
    """Figure-level polish: footer with source, optional suptitle, clean margins.

    Call as last step before `save_map`.

    `tight_bottom=True` shrinks the bottom margin so the footer sits right under
    the map — use it only when the scale bar is drawn *on* the map
    (`add_scalebar(ax, inside=True)`); with a below-map scale bar it would be
    clipped. Combine with `fit_figure_to_data` to also remove side/bottom
    whitespace from the aspect ratio.
    """
    from datetime import date as _date
    import matplotlib.lines as mlines
    _apply_rc()
    if date is None:
        date = _date.today().isoformat()

    fig.set_facecolor(STYLE["fig_bg"])

    if suptitle:
        # Stapel de suptitel (+ optionele subregel) met fysieke (inch) marges vanaf
        # de bovenrand, zodat de tussenruimte ook op een lage/brede figuur klopt —
        # vaste fracties (0.98/0.945) liepen daar over elkaar. De as-bovenrand `top`
        # zakt mee zodat de per-paneel titels vrij onder het suptitel-blok vallen.
        _fw, _fh = fig.get_size_inches()
        # Hoofdtitel groter dan de deelkaart-titels (STYLE["title_size"]) — zie de
        # invariant "Titelhiërarchie".
        sup_fs = STYLE["suptitle_size"]
        y_top_in = 0.16                                # marge boven de hoofdtitel (inch)
        fig.suptitle(suptitle, fontsize=sup_fs, fontweight=STYLE["suptitle_weight"],
                     color=STYLE["title_color"], x=0.05, ha="left",
                     y=1 - y_top_in / _fh, va="top")
        header_in = y_top_in + sup_fs / 72.0 + 0.10    # tot onder de suptitel + gap
        if suptitle_subtitle:
            fig.text(0.05, 1 - header_in / _fh, suptitle_subtitle,
                     fontsize=STYLE["subtitle_size"],
                     color=STYLE["subtitle_color"], ha="left", va="top")
            header_in += STYLE["subtitle_size"] / 72.0 + 0.14
        else:
            header_in += 0.10
        header_in += 0.42                              # ruimte voor de per-paneel titel
        top = 1 - header_in / _fh
    else:
        top = 0.94

    import matplotlib.text as mtext
    from matplotlib.transforms import ScaledTranslation

    footer_parts = [f"Bron: {source}", f"Datum: {date}"]
    if author:
        footer_parts.append(author)
    # Always disclose AI authorship in the footer.
    footer_parts.append("Disclaimer: deze kaart is gemaakt met AI.")
    publisher = "Gemeente Rotterdam"        # right-aligned at the map's right edge

    fs = STYLE["footer_size"]
    figw, figh = fig.get_size_inches()
    renderer = fig.canvas.get_renderer()

    def _wid(s):                            # rendered width of a footer string (inches)
        t = mtext.Text(0, 0, s, fontsize=fs)
        t.figure = fig
        return t.get_window_extent(renderer).width / fig.dpi

    joiner = "  ·  "
    avail = (0.95 - 0.05) * figw            # usable footer width (inches)
    gap = 0.15                              # min gap between left text and publisher
    raw = joiner.join(footer_parts)
    # Wrap units are the "·"-separated segments (also splits any "·" inside the
    # source itself, e.g. "Bron: … · Basiskaart: …"), so no single unit is too big.
    tokens = [t.strip() for t in raw.split("·") if t.strip()]

    if _wid(raw) + gap + _wid(publisher) <= avail:
        lines = [raw]                       # everything fits on one line
    else:
        # Not enough room -> wrap over multiple lines. The top line reserves space
        # for the right-aligned publisher; lower lines use the full width.
        lines, cur = [], ""
        budget = avail - _wid(publisher) - gap
        for tok in tokens:
            trial = tok if not cur else cur + joiner + tok
            if cur and _wid(trial) > budget:
                lines.append(cur)
                cur, budget = tok, avail
            else:
                cur = trial
        lines.append(cur)

    n = len(lines)
    line_in = fs / 72.0 * 1.7               # physical line pitch (inches)
    base = 0.02                             # bottom line baseline (figure fraction)

    # Draw lines stacked upward from the bottom with a fixed physical pitch (so the
    # spacing survives fit_figure_to_data resizing the figure height). i=0 is top.
    for i, ln in enumerate(lines):
        off = (n - 1 - i) * line_in
        tr = fig.transFigure + ScaledTranslation(0, off, fig.dpi_scale_trans)
        fig.text(0.05, base, ln, transform=tr, fontsize=fs,
                 color=STYLE["footer_color"], ha="left")
    top_off = (n - 1) * line_in
    trp = fig.transFigure + ScaledTranslation(0, top_off, fig.dpi_scale_trans)
    fig.text(0.95, base, publisher, transform=trp, fontsize=fs,
             color=STYLE["footer_color"], ha="right")

    # Separator just above the top footer line (0.04 for a single line; rises with
    # extra lines). The map bottom margin grows by the extra footer height.
    sep_y = max(0.04, base + (top_off + 0.55 * line_in) / figh)
    sep = mlines.Line2D([0.05, 0.95], [sep_y, sep_y],
                        color=STYLE["separator_color"], lw=0.5,
                        transform=fig.transFigure, figure=fig)
    fig.lines.append(sep)

    bottom = (0.05 if tight_bottom else 0.08) + (n - 1) * line_in / figh
    fig.subplots_adjust(left=pad, right=1 - pad, top=top, bottom=bottom)


def fit_figure_to_data(fig, ax) -> None:
    """Resize the figure *height* so an equal-aspect map fills the plotting area
    with no top/bottom whitespace.

    Call **after** `finalize_map` (so the subplot margins are final). Uses the
    data extent's aspect and the current subplot margins (`fig.subplotpars`);
    the width is kept, the height is recomputed. If a legend/list box is
    measured against the axes, draw it *after* this call.
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    dh = y1 - y0
    if dh <= 0:
        return
    data_aspect = (x1 - x0) / dh
    sp = fig.subplotpars
    w_frac = sp.right - sp.left
    h_frac = sp.top - sp.bottom
    if w_frac <= 0 or h_frac <= 0 or data_aspect <= 0:
        return
    figw, _ = fig.get_size_inches()
    fig.set_size_inches(figw, figw * w_frac / (data_aspect * h_frac))


def _data_axesfrac(ax, data):
    """(x, y) of `data` (GeoDataFrame or Nx2 array in RD coords) as axes fraction."""
    import numpy as np
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    if hasattr(data, "geometry"):
        p = data.geometry.representative_point()
        xs = (p.x.to_numpy() - x0) / (x1 - x0)
        ys = (p.y.to_numpy() - y0) / (y1 - y0)
    else:
        a = np.asarray(data, dtype=float)
        xs = (a[:, 0] - x0) / (x1 - x0)
        ys = (a[:, 1] - y0) / (y1 - y0)
    return xs, ys


def _flatten_avoid(data):
    """Flatten `data` (GeoDataFrame / GeoSeries / Nx2 point array / None, or a list
    of those) into a plain list of shapely geometries in data (RD) coords."""
    import numpy as np
    from shapely.geometry import Point
    out = []

    def _add(d):
        if d is None:
            return
        if isinstance(d, (list, tuple)):
            for x in d:
                _add(x)
        elif hasattr(d, "geometry"):        # GeoDataFrame
            out.extend(g for g in d.geometry.values if g is not None)
        elif hasattr(d, "geom_type"):       # GeoSeries
            out.extend(g for g in d.values if g is not None)
        else:                               # Nx2 point array
            a = np.asarray(d, dtype=float).reshape(-1, 2)
            out.extend(Point(float(x), float(y)) for x, y in a)

    _add(data)
    return out


def _axes_avoid_geometry(ax):
    """All plotted DATA geometry on the axes (data coords) for a legend to avoid
    automatically: scatter points, plotted lines and *filled* polygons. Excludes
    the basemap (`ax.images`) and the kaartelementen (`ax.patches`: north arrow,
    scale bar). Unfilled polygons count as their outline only, so a legend may
    still sit inside an unfilled boundary."""
    import numpy as np
    from matplotlib.collections import LineCollection
    from shapely.geometry import Point, LineString, Polygon
    geoms = []
    for coll in list(ax.collections):
        try:
            if isinstance(coll, LineCollection):
                geoms += [LineString(s) for s in coll.get_segments() if len(s) >= 2]
                continue
            offs = np.asarray(coll.get_offsets(), dtype=float)
            if offs.ndim == 2 and offs.shape[0] > 1:        # scatter: point positions
                geoms += [Point(x, y) for x, y in offs]
                continue
            fc = np.asarray(coll.get_facecolor())
            filled = fc.size and float(fc[:, 3].max()) > 0
            for path in coll.get_paths():
                if filled:
                    geoms += [Polygon(r).buffer(0) for r in path.to_polygons()
                              if len(r) >= 3]
                else:
                    v = np.asarray(path.vertices, dtype=float)
                    if len(v) >= 2:
                        geoms.append(LineString(v))
        except Exception:
            continue
    for ln in list(ax.lines):
        try:
            xy = np.column_stack([np.asarray(ln.get_xdata(), dtype=float),
                                  np.asarray(ln.get_ydata(), dtype=float)])
            if len(xy) >= 2:
                geoms.append(LineString(xy))
        except Exception:
            continue
    return [g for g in geoms if g is not None and not g.is_empty]


def _legend_spot(ax, lw, lh, data, *, mx, my):
    """Pick a spot for a legend box of size (lw, lh) in axes fraction that avoids
    both the data and the registered kaartelementen (scale bar / north arrow).

    It avoids **all plotted data layers** on the axes (scatter points, lines,
    filled polygons — auto-collected via `_axes_avoid_geometry`), never the basemap
    or the kaartelementen. Any explicit `data` (GeoDataFrame / Nx2 array / list of
    layers) is added on top. The box is tested against the real geometry, so a big
    polygon is avoided over its whole area, not just a centroid.

    Placement is a fixed priority (see invariant 8):
      1. **corner** — first free corner in order: lower left, upper left, lower
         right, upper right (a corner holding only a kaartelement is used just
         past it);
      2. **side** — otherwise slide along an edge to the first free spot; edges in
         order: left, right, bottom, top;
      3. **side panel** — otherwise signal `add_side_panel()`.

    Returns a dict:
      {'kind': 'corner', 'xy': (x0, y0)}     – a free corner,
      {'kind': 'float',  'xy': (x0, y0)}     – a free spot along an edge,
      {'kind': 'sidepanel', 'xy': (x0, y0)}  – nothing free; use a side panel.
    `xy` is the lower-left of the box in axes fraction.
    """
    import numpy as np
    fig = ax.figure
    x0d, x1d = ax.get_xlim()
    y0d, y1d = ax.get_ylim()
    aw = ax.get_window_extent().width / fig.dpi
    ah = ax.get_window_extent().height / fig.dpi
    reserved = _reserved_boxes(ax, aw, ah)

    # Everything to avoid: all data layers on the axes (auto) + any explicit data.
    geoms = _axes_avoid_geometry(ax) + _flatten_avoid(data)
    from shapely.geometry import box as _box
    tree = xs = ys = None
    only_pts = bool(geoms) and all(g.geom_type == "Point" for g in geoms)
    if only_pts:                                   # fast point-in-box path
        xy = np.array([(g.x, g.y) for g in geoms], dtype=float)
        xs = (xy[:, 0] - x0d) / (x1d - x0d)
        ys = (xy[:, 1] - y0d) / (y1d - y0d)
    elif geoms:                                    # lines/polygons -> spatial index
        from shapely import STRtree
        tree = STRtree(geoms)

    def _dbox(x0, y0):        # legend box (axes fraction) -> data-coord shapely box
        return _box(x0d + x0 * (x1d - x0d), y0d + y0 * (y1d - y0d),
                    x0d + (x0 + lw) * (x1d - x0d), y0d + (y0 + lh) * (y1d - y0d))

    def _overlap(x0, y0):
        if tree is not None:
            return int(tree.query(_dbox(x0, y0), predicate="intersects").size)
        if xs is None:
            return 0
        return int(((xs >= x0) & (xs <= x0 + lw) &
                    (ys >= y0) & (ys <= y0 + lh)).sum())

    # Edge margin as axes fraction: horizontal = LEGEND_MARGIN[0], vertical =
    # MARGIN_IN (fixed physical). The SAME margin is kept BETWEEN kaartelementen
    # (legend vs north arrow / scale bar): the reserved zones are inflated by it,
    # so the legend never touches another kaartelement (invariant 15).
    em_x, em_y = mx, MARGIN_IN / ah

    def _hits_furniture(x0, y0):
        return any(x0 < rx1 + em_x and x0 + lw > rx0 - em_x and
                   y0 < ry1 + em_y and y0 + lh > ry0 - em_y
                   for rx0, rx1, ry0, ry1 in reserved)

    base = {
        "lower left":  (em_x,          em_y),
        "upper left":  (em_x,          1 - em_y - lh),
        "lower right": (1 - em_x - lw, em_y),
        "upper right": (1 - em_x - lw, 1 - em_y - lh),
    }

    def _clear_furniture(name, x0, y0):
        """Nudge the box vertically just past any kaartelement it overlaps in this
        corner (scale bar / north arrow) **plus the margin**, so a corner stays
        usable (with the margin gap) when only a kaartelement sits in its corner."""
        for _ in range(4):
            hit = next(((ry0, ry1) for (rx0, rx1, ry0, ry1) in reserved
                        if x0 < rx1 + em_x and x0 + lw > rx0 - em_x
                        and y0 < ry1 + em_y and y0 + lh > ry0 - em_y), None)
            if hit is None:
                break
            y0 = (hit[1] + em_y) if "lower" in name else (hit[0] - em_y - lh)
        return x0, y0

    def _fits(x0, y0):
        return (em_y - 1e-6 <= y0 <= 1 - em_y - lh + 1e-6
                and not _hits_furniture(x0, y0) and not _overlap(x0, y0))

    # 1) CORNER method — prefer a corner, in order: lower left, upper left,
    #    lower right, upper right (a corner that only holds a kaartelement is
    #    used just past it + the margin).
    for name in ("lower left", "upper left", "lower right", "upper right"):
        x0, y0 = _clear_furniture(name, *base[name])
        if _fits(x0, y0):
            return {"kind": "corner", "xy": (x0, y0)}

    # 2) SIDE method — slide the legend along an edge to the first free spot;
    #    edges in order: left, right, bottom, top.
    gx = np.linspace(em_x, 1 - em_x - lw, 40)
    gy = np.linspace(em_y, 1 - em_y - lh, 40)
    for edge in (
        [(em_x, y) for y in gy],                 # left,   bottom -> top
        [(1 - em_x - lw, y) for y in gy],        # right,  bottom -> top
        [(x, em_y) for x in gx],                 # bottom, left -> right
        [(x, 1 - em_y - lh) for x in gx],        # top,    left -> right
    ):
        for (x0, y0) in edge:
            if _fits(x0, y0):
                return {"kind": "float", "xy": (x0, y0)}

    # 3) SIDE PANEL — no corner or edge is free; signal add_side_panel().
    return {"kind": "sidepanel", "xy": base["lower left"]}


def place_legend(ax, handles=None, labels=None, *, corner="auto", data=None,
                 title="Legenda", **legend_kwds):
    """Add a legend at a corner, styled per Rotterdam conventions (white box,
    bold left-aligned title, `LEGEND_MARGIN` inset).

    `corner`: 'upper right'|'upper left'|'lower right'|'lower left', or 'auto'.
    With 'auto' the legend must NEVER overlap the data: it avoids **all plotted
    layers** on the axes automatically (points, lines, filled polygons — never the
    basemap), plus any explicit `data` you pass, and places itself by the fixed
    priority of invariant 8: first free **corner** (lower left, upper left, lower
    right, upper right), else slide along an **edge** (left, right, bottom, top),
    else warn to use a **side panel** (`add_side_panel`). Returns the Legend.
    """
    mx, my = LEGEND_MARGIN
    kw = dict(frameon=True, facecolor=BOX_FACECOLOR, edgecolor=BOX_EDGECOLOR,
              framealpha=BOX_ALPHA, fontsize=9, title=title)
    kw.update(legend_kwds)
    # Proportional-symbol legends carry large markers; widen the handle cell so
    # big circles sit inside the frame instead of spilling over the left edge.
    if handles is not None:
        fs = float(kw.get("fontsize", 9))
        msz = [h.get_markersize() for h in handles
               if hasattr(h, "get_markersize") and h.get_markersize()]
        if msz:
            need = max(msz) / fs + 0.4          # handle cell size in fontsize units
            kw.setdefault("handlelength", need)
            kw.setdefault("handleheight", need)
    anc = _legend_anchor(ax, corner if corner != "auto" else "upper right")
    if handles is not None:
        leg = ax.legend(handles=handles, labels=labels, **{**kw, **anc})
    else:
        leg = ax.legend(**{**kw, **anc})
    leg.get_frame().set_linewidth(BOX_LINEWIDTH)
    leg.set_alignment("left")
    if leg.get_title().get_text():
        leg.get_title().set_fontweight("bold")

    if corner == "auto":
        fig = ax.figure
        fig.canvas.draw()
        bb = leg.get_window_extent(fig.canvas.get_renderer()).transformed(
            ax.transAxes.inverted())
        spot = _legend_spot(ax, bb.width, bb.height, data, mx=mx, my=my)
        if spot["kind"] == "sidepanel":
            import warnings
            warnings.warn("place_legend: no free corner or edge; the legend "
                          "overlaps data. Use add_side_panel() instead.",
                          stacklevel=2)
        leg.set_loc("lower left")          # anchor = box lower-left, in axes fraction
        leg.set_bbox_to_anchor(spot["xy"], transform=ax.transAxes)
    return leg


def add_proportional_legend(ax, values, sizes, *, title="Legenda",
                            corner="auto", data=None, facecolor="#2c7fb8",
                            edgecolor="#0b3d5c", alpha=0.55, fontsize=9,
                            gap_in: float = 0.16, fmt=None):
    """Proportional-circle size legend with **equal vertical whitespace** between
    the circles (constant edge-to-edge gap, so the spacing looks even even though
    the circles differ in size — matplotlib's own legend can only equalise the
    circle *centres*, which leaves uneven gaps).

    `values` : label per circle (numbers or strings, any order),
    `sizes`  : matching scatter areas — the same `s` you passed to `ax.scatter`,
               so the legend circles are exactly the plotted sizes,
    `fmt`    : optional formatter for numeric `values` (default NL thousands).

    Circles are stacked largest-at-the-bottom at a fixed physical size on a fitted
    white box, auto-placed like `place_legend` (corner -> edge -> side panel; see
    invariant 8). Call **after** the
    scale bar / north arrow. Returns the box.
    """
    import numpy as np
    from matplotlib.patches import Circle, Rectangle
    from matplotlib.text import Text
    from matplotlib.transforms import ScaledTranslation
    fig = ax.figure
    mx, my = LEGEND_MARGIN
    if fmt is None:
        def fmt(v):
            return nl_getal(v) if isinstance(v, (int, float)) else str(v)

    # smallest -> largest, so the biggest circle sits at the bottom of the stack
    idx = list(np.argsort(sizes))
    vals = [values[i] for i in idx]
    szs = [sizes[i] for i in idx]
    diam = [float(np.sqrt(s)) / 72.0 for s in szs]   # scatter s (pt^2) -> diameter (inch)
    rad = [d / 2 for d in diam]
    rmax = max(rad)

    fig.canvas.draw()
    rend = fig.canvas.get_renderer()

    def _txt_w(s, weight="normal"):
        t = Text(0, 0, s, fontsize=fontsize, fontweight=weight)
        t.figure = fig
        return t.get_window_extent(rend).width / fig.dpi

    lab_w = max(_txt_w(fmt(v)) for v in vals)
    title_w = _txt_w(str(title), "bold") if title else 0.0
    title_h = fontsize * 1.5 / 72.0 if title else 0.0

    P = 0.14                 # inner padding (inch)
    title_gap = 0.10 if title else 0.0
    label_gap = 0.14         # circle edge -> label text
    G = gap_in               # equal edge-to-edge gap between circles
    cx = P + rmax            # common vertical centre line for the circles
    label_x = P + 2 * rmax + label_gap

    circles_h = sum(diam) + G * (len(diam) - 1)
    H = P + title_h + title_gap + circles_h + P
    W = max(label_x + lab_w, P + title_w) + P

    # find a spot (axes fraction), then draw everything in inches anchored there
    aw = ax.get_window_extent().width / fig.dpi
    ah = ax.get_window_extent().height / fig.dpi
    dat = data if data is not None else np.empty((0, 2))
    spot = _legend_spot(ax, W / aw, H / ah, dat, mx=mx, my=my)
    if spot["kind"] == "sidepanel":
        import warnings
        warnings.warn("add_proportional_legend: no free corner or edge; "
                      "use add_side_panel().", stacklevel=2)
    x0, y0 = spot["xy"]
    tr = fig.dpi_scale_trans + ScaledTranslation(x0, y0, ax.transAxes)

    box = Rectangle((0, 0), W, H, transform=tr, facecolor=BOX_FACECOLOR,
                    alpha=BOX_ALPHA, edgecolor=BOX_EDGECOLOR,
                    linewidth=BOX_LINEWIDTH, zorder=9, clip_on=False)
    ax.add_patch(box)
    if title:
        ax.text(P, H - P, str(title), transform=tr, ha="left", va="top",
                fontsize=fontsize, fontweight="bold", color="#222222",
                zorder=11, clip_on=False)
    yt = H - P - title_h - title_gap        # top of the circle stack
    for v, d, r in zip(vals, diam, rad):
        ccy = yt - r
        ax.add_patch(Circle((cx, ccy), r, transform=tr, facecolor=facecolor,
                            edgecolor=edgecolor, linewidth=0.6, alpha=alpha,
                            zorder=10, clip_on=False))
        ax.text(label_x, ccy, fmt(v), transform=tr, ha="left", va="center",
                fontsize=fontsize, color="#222222", zorder=11, clip_on=False)
        yt = ccy - r - G
    return box


def _swatch_legend_metrics(fig, colors, labels, *, title="Legenda",
                           legendakop=None, fontsize=9):
    """Bereken de layout-maten (inch) van de kleurstaal-legenda die
    ``add_swatch_legend`` tekent, zonder te tekenen. Retourneert o.a. ``W`` (de
    breedte) zodat een zijpaneel exact op de legendabreedte gemaakt kan worden.
    Gedeeld door ``add_swatch_legend`` en ``add_swatch_legend_sidepanel``.
    """
    from matplotlib.text import Text
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    kop_fs = fontsize                        # legendakop: same size/style as labels

    def _tw(s, fs, weight="normal"):
        t = Text(0, 0, s, fontsize=fs, fontweight=weight)
        t.figure = fig
        return t.get_window_extent(rend).width / fig.dpi

    n = len(labels)
    P = 0.14                                 # inner padding (inch)
    title_h = fontsize * 1.5 / 72.0
    title_gap = 0.05
    kop_h = kop_fs * 1.4 / 72.0 if legendakop else 0.0
    kop_gap = 0.09 if legendakop else 0.0
    sw = fontsize * 1.15 / 72.0              # swatch side (inch)
    row_h, row_gap, label_gap = sw, 0.09, 0.10
    label_x = P + sw + label_gap

    lab_w = max(_tw(str(l), fontsize) for l in labels)
    title_w = _tw(str(title), fontsize, "bold") if title else 0.0
    kop_w = _tw(str(legendakop), kop_fs) if legendakop else 0.0

    rows_total = n * row_h + (n - 1) * row_gap
    H = P + title_h + title_gap + kop_h + kop_gap + rows_total + P
    W = max(label_x + lab_w, P + title_w, P + kop_w) + P
    return dict(P=P, title_h=title_h, title_gap=title_gap, kop_h=kop_h,
                kop_gap=kop_gap, sw=sw, row_h=row_h, row_gap=row_gap,
                label_x=label_x, W=W, H=H)


def add_swatch_legend(ax, colors, labels, *, title="Legenda", legendakop=None,
                      corner="auto", data=None, edgecolor="#555555",
                      fontsize=9):
    """Categorical / choropleth legend: a bold **title**, an optional **non-bold
    legendakop** line between the title and the classes (e.g. the unit of the
    mapped variable; same size/style as the class labels), then one colour swatch
    + label per class on a fitted white box.

    matplotlib's own legend title cannot carry a differently-styled second line,
    so this draws the legend itself (like `add_proportional_legend`). `colors` and
    `labels` are equal-length. Auto-placed like `place_legend` (corner -> edge ->
    side panel); call **after** the scale bar / north arrow. Returns box.
    """
    import numpy as np
    from matplotlib.patches import Rectangle
    from matplotlib.transforms import ScaledTranslation
    fig = ax.figure
    mx, my = LEGEND_MARGIN
    kop_fs = fontsize                        # legendakop: same size/style as labels

    # Layout-maten (inch); gedeeld met _swatch_legend_metrics.
    _m = _swatch_legend_metrics(fig, colors, labels, title=title,
                                legendakop=legendakop, fontsize=fontsize)
    P = _m["P"]
    title_h, title_gap = _m["title_h"], _m["title_gap"]
    kop_h, kop_gap = _m["kop_h"], _m["kop_gap"]
    sw, row_h, row_gap = _m["sw"], _m["row_h"], _m["row_gap"]
    label_x, W, H = _m["label_x"], _m["W"], _m["H"]

    aw = ax.get_window_extent().width / fig.dpi
    ah = ax.get_window_extent().height / fig.dpi
    dat = data if data is not None else np.empty((0, 2))
    spot = _legend_spot(ax, W / aw, H / ah, dat, mx=mx, my=my)
    if spot["kind"] == "sidepanel":
        import warnings
        warnings.warn("add_swatch_legend: no free corner or edge; "
                      "use add_side_panel().", stacklevel=2)
    x0, y0 = spot["xy"]
    tr = fig.dpi_scale_trans + ScaledTranslation(x0, y0, ax.transAxes)

    box = Rectangle((0, 0), W, H, transform=tr, facecolor=BOX_FACECOLOR,
                    alpha=BOX_ALPHA, edgecolor=BOX_EDGECOLOR,
                    linewidth=BOX_LINEWIDTH, zorder=9, clip_on=False)
    ax.add_patch(box)
    y = H - P
    if title:
        ax.text(P, y, str(title), transform=tr, ha="left", va="top",
                fontsize=fontsize, fontweight="bold", color="#222222",
                zorder=11, clip_on=False)
        y -= title_h + title_gap
    if legendakop:
        ax.text(P, y, str(legendakop), transform=tr, ha="left", va="top",
                fontsize=kop_fs, fontweight="normal", color="#222222",
                zorder=11, clip_on=False)
        y -= kop_h + kop_gap
    for i, (c, lab) in enumerate(zip(colors, labels)):
        rc = (y - i * (row_h + row_gap)) - row_h / 2.0     # row centre
        ax.add_patch(Rectangle((P, rc - sw / 2.0), sw, sw, transform=tr,
                               facecolor=c, edgecolor=edgecolor, linewidth=0.4,
                               zorder=10, clip_on=False))
        ax.text(label_x, rc, str(lab), transform=tr, ha="left", va="center",
                fontsize=fontsize, color="#222222", zorder=11, clip_on=False)
    return box


def add_side_panel(fig, ax, *, width_in: float = 3.2, gap_in: float = 0.15):
    """Widen the figure and add a blank panel axes to the right of the map, for a
    legend or long list that would otherwise overlap the data. The map keeps its
    size and aspect (the figure just gets wider). Call **after** `finalize_map`
    (and `fit_figure_to_data`). Returns the panel axes (axis off); draw a legend
    or `panel.text(...)` into it using its own [0, 1] coordinates.
    """
    figw, figh = fig.get_size_inches()
    pos = ax.get_position()
    mx0, mw = pos.x0 * figw, pos.width * figw     # map box in inches
    my0, mh = pos.y0 * figh, pos.height * figh
    new_w = figw + width_in + gap_in
    fig.set_size_inches(new_w, figh)
    ax.set_position([mx0 / new_w, my0 / figh, mw / new_w, mh / figh])
    panel = fig.add_axes([(mx0 + mw + gap_in) / new_w, my0 / figh,
                          width_in / new_w, mh / figh])
    panel.set_axis_off()
    return panel


def fit_side_panel(fig, ax, panel, *, margin_in=0.15):
    """Krimp de breedte van een zijpaneel (van ``add_side_panel``) tot de
    **werkelijk getekende inhoud + marge** en versmal de figuur navenant, zodat
    er geen lege ruimte naast de paneelinhoud overblijft. De kaart-as blijft
    ongewijzigd; de footer/scheidingslijn (op figuur-fracties) schuiven mee.

    Nodig omdat ``save_map``'s ``bbox_inches="tight"`` de **volle paneel-as**
    meerekent (een onzichtbaar achtergrondvlak of `frame_off` verandert dat niet)
    en de footer tot ~0.95 van de figuurbreedte loopt — alleen een smaller paneel
    haalt de witruimte echt weg. Roep aan **ná** alle paneelinhoud + ``finalize_map``
    / ``fit_figure_to_data``, vlak vóór ``save_map``. Retourneert het paneel.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    figw, figh = fig.get_size_inches()
    ppos, mpos = panel.get_position(), ax.get_position()
    px0i = ppos.x0 * figw
    mx0i, mwi = mpos.x0 * figw, mpos.width * figw

    skip = {panel.patch, panel.xaxis, panel.yaxis, *panel.spines.values()}
    right = px0i
    children = list(panel.get_children())
    leg = panel.get_legend()
    if leg is not None:
        children.append(leg)
    for ch in children:
        if ch in skip or not ch.get_visible():
            continue
        try:
            bb = ch.get_window_extent(r)
        except Exception:
            continue
        if bb.width > 0 and bb.height > 0:
            right = max(right, bb.x1 / fig.dpi)

    pw_new = max(0.1, (right - px0i) + margin_in)
    new_w = px0i + pw_new
    if new_w >= figw - 1e-3:
        return panel                          # niets te winnen
    fig.set_size_inches(new_w, figh)
    ax.set_position([mx0i / new_w, mpos.y0, mwi / new_w, mpos.height])
    panel.set_position([px0i / new_w, ppos.y0, pw_new / new_w, ppos.height])
    return panel


def add_swatch_legend_sidepanel(fig, ax, colors, labels, *, title="Legenda",
                                legendakop=None, fontsize=9, gap_in=0.15):
    """Teken een kleurstaal-legenda in een zijpaneel dat **precies zo breed is
    als de legenda + marge** — dus geen overbodige witruimte rechts. De totale
    figuurbreedte wordt zo kaart + gap + legendabreedte + marge.

    Gebruik dit i.p.v. los ``add_side_panel`` + ``add_swatch_legend`` wanneer de
    legenda niet in een hoek/rand van de kaart past (invariant 8). Roep aan **ná**
    ``finalize_map`` / ``fit_figure_to_data``. Retourneert de paneel-as.
    """
    import warnings
    mx = LEGEND_MARGIN[0]
    metrics = _swatch_legend_metrics(fig, colors, labels, title=title,
                                     legendakop=legendakop, fontsize=fontsize)
    # Ruim genoeg paneel zodat de legenda-box past; fit_side_panel trimt daarna
    # exact tot de box + marge (kaart + gap + legendabreedte + marge).
    panel = add_side_panel(fig, ax, width_in=metrics["W"] / (1 - 2 * mx),
                           gap_in=gap_in)
    with warnings.catch_warnings():
        # In een zijpaneel is de "no free corner"-melding verwacht gedrag.
        warnings.filterwarnings("ignore", message="add_swatch_legend: no free")
        add_swatch_legend(panel, colors, labels, title=title,
                          legendakop=legendakop, fontsize=fontsize)
    fit_side_panel(fig, ax, panel)
    return panel


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
