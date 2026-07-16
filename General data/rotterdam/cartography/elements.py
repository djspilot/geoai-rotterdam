"""Kaartelementen: schaalstok, noordpijl en hun gereserveerde zones."""
from __future__ import annotations

from ._base import *

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


