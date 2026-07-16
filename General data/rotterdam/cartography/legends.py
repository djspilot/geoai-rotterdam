"""Legenda's: auto-plaatsing, kleurstaal-/proportionele legenda en zijpanelen."""
from __future__ import annotations

from ._base import *
from .elements import _reserved_boxes

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


