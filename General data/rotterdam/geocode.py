"""PDOK geocoder and CBS Wijk-en-Buurtkaart helpers."""

from __future__ import annotations

import json
import urllib.request
from urllib.parse import quote, urlencode

import geopandas as gpd

from .vocab import RD_NEW


def pdok_geocode(query: str, rows: int = 5) -> list[dict]:
    """PDOK Locatieserver free-text search. No key required.

    Returns docs with `id`, `type`, `weergavenaam`, `centroide_ll`, `centroide_rd`.
    """
    url = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?" + urlencode({
        "q": query, "rows": str(rows),
        "fl": "id,type,weergavenaam,centroide_ll,centroide_rd",
    })
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8")).get("response", {}).get("docs", [])


def pdok_geocode_rd(query: str) -> tuple[float, float] | None:
    """Convenience: best hit as (x, y) in EPSG:28992, or None."""
    hits = pdok_geocode(query, rows=1)
    if not hits:
        return None
    rd = hits[0].get("centroide_rd", "")
    if not rd.startswith("POINT("):
        return None
    x, y = rd.replace("POINT(", "").rstrip(")").split()
    return float(x), float(y)


def cbs_buurten_rotterdam(year: int = 2024, *,
                          drop_empty: bool = True) -> gpd.GeoDataFrame:
    """CBS Wijk- en Buurtkaart restricted to Rotterdam.

    Use `aantal_inwoners` to normalise choropleths (also `aantalInwoners`, the
    native CBS field name since ~2023).

    `drop_empty=True` (default) keeps only buurten with inhabitants (drops the CBS
    secrecy code -99999999 and 0-inhabitant buurten). Set `drop_empty=False` to
    get **all** Rotterdam buurten incl. the empty port/industrial ones — useful to
    render "geen gegevens" polygons or to measure the full municipal extent.
    """
    # NB: this PDOK WFS ignores CQL_FILTER (and `gpd.read_file(url)` lets GDAL
    # re-issue an unfiltered, paged WFS request). So fetch the bytes ourselves
    # for a bbox around Rotterdam (bbox IS honoured) and filter locally on
    # gemeentenaam. Rotterdam RD extent, with margin:
    import io
    bbox = "55000,428000,102000,448000,EPSG:28992"
    url = (
        f"https://service.pdok.nl/cbs/wijkenbuurten/{year}/wfs/v1_0"
        "?service=WFS&version=2.0.0&request=GetFeature"
        "&typeNames=wijkenbuurten:buurten&outputFormat=application/json"
        "&srsName=EPSG:28992&count=5000&bbox=" + bbox
    )
    raw = urllib.request.urlopen(url, timeout=120).read()
    gdf = gpd.read_file(io.BytesIO(raw)).to_crs(RD_NEW)
    # CBS renamed snake_case -> camelCase; keep a backward-compatible alias.
    inw = "aantalInwoners" if "aantalInwoners" in gdf.columns else "aantal_inwoners"
    gdf["aantal_inwoners"] = gdf[inw]
    gdf = gdf[gdf["gemeentenaam"] == "Rotterdam"]
    if drop_empty:
        gdf = gdf[gdf["aantal_inwoners"] > 0]
    return gdf.copy()


def nwb_wegvakken(bbox: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    """NWB (Nationaal Wegenbestand, Rijkswaterstaat) wegvakken from the PDOK WFS,
    within `bbox` = (minx, miny, maxx, maxy) in EPSG:28992.

    The service is paginated (WFS caps at 1000 features per request), so this
    walks `startIndex` until exhausted. Returns a GeoDataFrame in EPSG:28992
    (MultiLineString); clip to your area of interest yourself.

    Useful attributes: `sttNaam` (straatnaam), `wegnummer`, `wegbehnaam`
    (wegbeheerder), `wegtype`/`wgtypeOms` (leeg voor gemeentelijke wegen),
    `bstCode` (baansoort: RB=rijbaan, FP=fietspad, VP=voetpad, BUS=busbaan, …),
    `frc` (functional road class), `fow` (form of way).

    Endpoint: service.pdok.nl/rws/nationaal-wegenbestand-wegen/wfs/v1_0
    (feature type `nwbwegen:wegvakken`; zie ook `national_sources.md`).
    """
    import io

    import pandas as pd

    minx, miny, maxx, maxy = (round(v) for v in bbox)
    base = (
        "https://service.pdok.nl/rws/nationaal-wegenbestand-wegen/wfs/v1_0"
        "?service=WFS&version=2.0.0&request=GetFeature"
        "&typeNames=nwbwegen:wegvakken&outputFormat=application/json"
        f"&srsName=EPSG:{RD_NEW}&count=1000"
        f"&bbox={minx},{miny},{maxx},{maxy},EPSG:{RD_NEW}"
    )
    parts: list = []
    start = 0
    while True:
        raw = urllib.request.urlopen(base + f"&startIndex={start}", timeout=120).read()
        g = gpd.read_file(io.BytesIO(raw))
        if len(g) == 0:
            break
        parts.append(g)
        start += len(g)
        if len(g) < 1000:
            break
    if not parts:
        return gpd.GeoDataFrame(geometry=[], crs=RD_NEW)
    return gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=RD_NEW).to_crs(RD_NEW)
