"""TIR area filtering and per-polygon counting.

`filter_to_area` hides the attribute-filter-then-spatial-join pattern that
was duplicated across ~16 scripts. Pass `gebied_names` for gebied-level
clipping or `buurt_names` (with the buurten layer) for buurt-level.
"""

from __future__ import annotations

from typing import Sequence

import geopandas as gpd
import pandas as pd

from .loader import require_columns


def filter_to_area(
    assets: gpd.GeoDataFrame,
    gebieden: gpd.GeoDataFrame,
    *,
    gebied_names: Sequence[str] | None = None,
    buurt_names: Sequence[str] | None = None,
    buurten: gpd.GeoDataFrame | None = None,
) -> gpd.GeoDataFrame:
    """Spatially clip assets to one or more gebieden / buurten.

    Both inputs must be in EPSG:28992. Returns features within the union of
    the named polygons.
    """
    if gebied_names:
        require_columns(gebieden, ["GEBDNAAM"], "gebieden")
        polys = gebieden.loc[gebieden["GEBDNAAM"].isin(gebied_names)]
    elif buurt_names:
        if buurten is None:
            raise ValueError("Pass `buurten` GeoDataFrame when filtering by buurt_names")
        require_columns(buurten, ["BUURTNAAM"], "buurten")
        polys = buurten[buurten["BUURTNAAM"].isin(buurt_names)]
    else:
        raise ValueError("Pass gebied_names or buurt_names")
    if polys.empty:
        raise ValueError(f"Geen gebieden/buurten gevonden voor {gebied_names or buurt_names}")
    joined = gpd.sjoin(assets, polys[["geometry"]], predicate="within", how="inner")
    return joined.drop(columns=[c for c in joined.columns if c.startswith("index_")])


def count_per_polygon(
    points: gpd.GeoDataFrame,
    polygons: gpd.GeoDataFrame,
    *,
    key: str,
    normalize_by: str | None = None,
    per: int = 1000,
) -> gpd.GeoDataFrame:
    """Spatial-join points to polygons, count per `key`, optionally normalize.

    Returns polygons with extra columns `n` and (if normalized) `rate`.
    """
    joined = gpd.sjoin(points, polygons[[key, "geometry"]],
                       predicate="within", how="inner")
    counts = joined.groupby(key).size().reset_index(name="n")
    out = polygons.merge(counts, on=key, how="left").fillna({"n": 0})
    if normalize_by:
        out["rate"] = out["n"] / out[normalize_by].replace({0: pd.NA}) * per
    return out
