"""Basemaps: PDOK BRT en de Rotterdamse huisstijl-basemaps."""
from __future__ import annotations

from ._base import *

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

    from ..arcgis import _ssl_context

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


