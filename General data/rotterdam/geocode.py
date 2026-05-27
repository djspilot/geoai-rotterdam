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


def cbs_buurten_rotterdam(year: int = 2024) -> gpd.GeoDataFrame:
    """CBS Wijk- en Buurtkaart restricted to Rotterdam.

    Use `aantal_inwoners` to normalise choropleths. Filters out CBS secrecy
    code -99999999.
    """
    url = (
        f"https://service.pdok.nl/cbs/wijkenbuurten/{year}/wfs/v1_0"
        "?service=WFS&version=2.0.0&request=GetFeature"
        "&typeNames=wijkenbuurten:buurten&outputFormat=application/json"
        "&CQL_FILTER=" + quote("gemeentenaam='Rotterdam'")
    )
    gdf = gpd.read_file(url).to_crs(RD_NEW)
    return gdf[gdf["aantal_inwoners"] > 0].copy()
