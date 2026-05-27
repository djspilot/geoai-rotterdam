"""Load Rotterdam GeoJSON layers and coerce them to EPSG:28992 (RD New).

The Rotterdam ArcGIS exports often claim WGS84 in metadata but contain RD
coordinates. `load_rotterdam` detects this from the bounds and overrides the
CRS without reprojecting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import geopandas as gpd
import pandas as pd

from .vocab import LOCAL_FILES, RD_NEW


def load_rotterdam(path: str | Path) -> gpd.GeoDataFrame:
    """Read a Rotterdam GeoJSON and normalise to EPSG:28992."""
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=RD_NEW, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=RD_NEW)
    return gdf if gdf.crs.to_epsg() == RD_NEW else gdf.to_crs(epsg=RD_NEW)


def load_layer(name: str) -> gpd.GeoDataFrame:
    """Load a known local layer by short name. See `vocab.LOCAL_FILES`."""
    if name == "bomen":
        import glob
        chunks = glob.glob(LOCAL_FILES["bomen_chunks_glob"])
        if not chunks:
            raise FileNotFoundError(
                f"No bomen chunks found at {LOCAL_FILES['bomen_chunks_glob']}"
            )
        gdf = pd.concat([gpd.read_file(c) for c in chunks], ignore_index=True)
        return gpd.GeoDataFrame(gdf, geometry="geometry", crs=f"EPSG:{RD_NEW}")
    if name not in LOCAL_FILES:
        raise KeyError(f"Unknown layer '{name}'. Known: {list(LOCAL_FILES)}")
    return load_rotterdam(LOCAL_FILES[name])


def require_columns(gdf: gpd.GeoDataFrame, columns: Sequence[str], name: str) -> None:
    missing = [c for c in columns if c not in gdf.columns]
    if missing:
        raise KeyError(f"{name} mist kolommen: {missing}")


def require_paths(paths: Iterable[str | Path]) -> None:
    missing = [str(p) for p in paths if not Path(p).exists()]
    if missing:
        raise FileNotFoundError(f"Ontbrekende databronnen: {missing}")


def safe_centroids(gdf: gpd.GeoDataFrame):
    """Yield (row, centroid) tuples, skipping null/empty geometries."""
    for _, row in gdf.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        c = row.geometry.centroid
        if c.is_empty:
            continue
        yield row, c
