"""Kaart Terbregge: afvalbakken + knelpunten + stratenpatroon (Wegvakonderdelen)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import requests

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "General data" / "Data"
OUT = PROJECT / "output"

WIJK_NAAM = "Terbregge"
SERVICE_RADIUS_M = 150
MIN_KNELPUNT_M2 = 7_500
WEGVAK_LAYER = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Wegvakonderdelen/MapServer/0/query"
BATCH_SIZE = 2000


def load_rotterdam(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def fetch_json(params: dict[str, Any]) -> dict[str, Any]:
    r = requests.get(WEGVAK_LAYER, params=params, timeout=90, verify=False)
    r.raise_for_status()
    return r.json()


def download_straten_wijk(wijk_naam: str) -> gpd.GeoDataFrame:
    where = f"WIJK = '{wijk_naam}'"
    count_payload = fetch_json({"where": where, "returnCountOnly": "true", "f": "json"})
    count = int(count_payload.get("count") or 0)
    print(f"Wegvakonderdelen op attribuutfilter WIJK={wijk_naam}: {count}")

    if count == 0:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:28992")

    features: list[dict[str, Any]] = []
    batches = math.ceil(count / BATCH_SIZE)
    for i in range(batches):
        offset = i * BATCH_SIZE
        n = min(BATCH_SIZE, count - offset)
        batch = fetch_json(
            {
                "where": where,
                "outFields": "WIJK,STRAAT,WEGVAKNUMMER,ONDERDEELTYPE",
                "returnGeometry": "true",
                "outSR": "28992",
                "resultOffset": str(offset),
                "resultRecordCount": str(n),
                "f": "geojson",
            }
        )
        features.extend(batch.get("features", []))

    gdf = gpd.GeoDataFrame.from_features(features)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=28992)
    elif gdf.crs.to_epsg() != 28992:
        gdf = gdf.to_crs(epsg=28992)
    return gdf


def add_scale_bar(ax, length_m=500):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222", linewidth=2.0)
    ax.plot([x0, x0], [y0 - 40, y0 + 40], color="#222", linewidth=1.4)
    ax.plot([x1, x1], [y0 - 40, y0 + 40], color="#222", linewidth=1.4)
    ax.text((x0 + x1) / 2, y0 + 90, "500 m", ha="center", va="bottom", fontsize=9)


def main() -> None:
    OUT.mkdir(exist_ok=True)

    buurten = load_rotterdam(DATA / "tir_buurten.geojson")
    afval = load_rotterdam(DATA / "afvalbak.geojson")

    wijk = buurten[buurten["BUURTNAAM"] == WIJK_NAAM].copy()
    if wijk.empty:
        raise ValueError(f"Wijk '{WIJK_NAAM}' niet gevonden")
    wijk["geometry"] = wijk.geometry.make_valid()

    afval_attr = afval[afval["WIJK"] == WIJK_NAAM].copy()
    afval_wijk = gpd.sjoin(afval_attr, wijk[["BUURTNAAM", "geometry"]], how="inner", predicate="within")
    afval_wijk = afval_wijk[[c for c in ["WOONPLAATS", "WIJK", "STRAAT", "TYPE", "geometry"] if c in afval_wijk.columns]].copy()

    # Knelpunten o.b.v. 150m afstand tot dichtstbijzijnde afvalbak
    wijk_union = wijk.union_all()
    if len(afval_wijk) > 0:
        service_union = afval_wijk.geometry.buffer(SERVICE_RADIUS_M).union_all()
        uncovered = wijk_union.difference(service_union)
    else:
        uncovered = wijk_union

    if uncovered.is_empty:
        knelpunten = gpd.GeoDataFrame({"opp_m2": []}, geometry=[], crs="EPSG:28992")
    else:
        parts = list(uncovered.geoms) if uncovered.geom_type == "MultiPolygon" else [uncovered]
        knelpunten = gpd.GeoDataFrame(geometry=parts, crs="EPSG:28992")
        knelpunten["opp_m2"] = knelpunten.area
        knelpunten = knelpunten[knelpunten["opp_m2"] >= MIN_KNELPUNT_M2].copy()

    # Stratenpatroon uit gemeentelijke wegvakonderdelen
    straten = download_straten_wijk(WIJK_NAAM)
    if not straten.empty:
        straten = gpd.clip(straten, wijk[["geometry"]])

    if not knelpunten.empty and not straten.empty:
        straten_knel = gpd.overlay(straten[["geometry"]], knelpunten[["geometry"]], how="intersection")
        opp_straten_knel_m2 = float(straten_knel.area.sum())
    else:
        opp_straten_knel_m2 = 0.0

    print(f"Afvalbakken in {WIJK_NAAM}: {len(afval_wijk)}")
    print(f"Knelpuntzones: {len(knelpunten)}")
    print(f"Wegoppervlak binnen knelpuntzones: {opp_straten_knel_m2:,.0f} m2")

    straten_out = OUT / "stratenpatroon_terbregge.geojson"
    map_out = OUT / "kaart_afvalbakken_knelpunten_straten_terbregge.png"
    straten.to_file(straten_out, driver="GeoJSON")

    fig, ax = plt.subplots(figsize=(12, 10))
    wijk.plot(ax=ax, color="#f5f2ec", edgecolor="#8b8275", linewidth=1.0, zorder=1)

    if not knelpunten.empty:
        knelpunten.plot(ax=ax, color="#ffd166", edgecolor="#e09f00", linewidth=0.8, alpha=0.72, zorder=2)

    if not straten.empty:
        straten.boundary.plot(ax=ax, color="#5f6b73", linewidth=0.55, alpha=0.85, zorder=3)

    if len(afval_wijk) > 0:
        afval_wijk.plot(ax=ax, color="#d94841", markersize=20, alpha=0.9, zorder=4)

    add_scale_bar(ax)
    handles = [
        mpatches.Patch(facecolor="#f5f2ec", edgecolor="#8b8275", label="Wijk Terbregge"),
        mlines.Line2D([], [], color="#5f6b73", linewidth=2, label="Stratenpatroon"),
        mlines.Line2D([], [], color="#d94841", marker="o", linestyle="None", markersize=8, label=f"Afvalbakken ({len(afval_wijk)})"),
        mpatches.Patch(facecolor="#ffd166", edgecolor="#e09f00", label=f"Knelpunt (>{SERVICE_RADIUS_M}m van afvalbak)"),
    ]
    ax.legend(handles=handles, title="Legenda", loc="lower right", frameon=True, framealpha=0.95)

    ax.set_title(
        f"Afvalbakken, knelpunten en stratenpatroon in {WIJK_NAAM}",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )
    ax.text(
        0.5,
        0.03,
        f"Afvalbakken: {len(afval_wijk)} | Knelpunten: {len(knelpunten)} | Wegoppervlak in knelpunt: {opp_straten_knel_m2:,.0f} m2",
        transform=fig.transFigure,
        ha="center",
        fontsize=10,
        color="#555",
    )
    ax.set_axis_off()
    plt.tight_layout()
    fig.savefig(map_out, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"GeoJSON opgeslagen: {straten_out}")
    print(f"Kaart opgeslagen: {map_out}")


if __name__ == "__main__":
    main()
