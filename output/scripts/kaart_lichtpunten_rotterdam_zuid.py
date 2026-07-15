"""Statische kaart: alle lichtpunten in Rotterdam Zuid."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import requests

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA = Path("General data/Data")
OUT = Path("output")
API_LAYER = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/LICHTPUNTEN/MapServer/0/query"
BATCH_SIZE = 2000

# Deze afbakening wordt in dit project eerder gebruikt voor Rotterdam Zuid.
ZUID_GEBIEDEN = [
    "Feijenoord",
    "IJsselmonde",
    "Charlois",
    "Hoogvliet",
    "Pernis",
    "Rozenburg",
    "Waalhaven-Eemhaven",
    "Vondelingenplaat",
]


def load_rd(path: Path) -> gpd.GeoDataFrame:
    """Load GeoJSON and normalize CRS to EPSG:28992 (RD New)."""
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds

    # Sommige lokale bestanden hebben RD-coordinaten maar CRS-label EPSG:4326.
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)

    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def enforce_rd_crs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Detect likely CRS from bounds and normalize to EPSG:28992."""
    if gdf.empty:
        return gdf.set_crs(epsg=28992)

    minx, miny, _, _ = gdf.total_bounds
    if gdf.crs is None:
        if -180 <= minx <= 180 and -90 <= miny <= 90:
            gdf = gdf.set_crs(epsg=4326)
        else:
            gdf = gdf.set_crs(epsg=28992)

    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def where_clause(gebieden: list[str]) -> str:
    quoted = ", ".join(f"'{naam}'" for naam in gebieden)
    return f"WOONPLAATS IN ({quoted})"


def fetch_json(params: dict[str, Any]) -> dict[str, Any]:
    resp = requests.get(API_LAYER, params=params, timeout=90, verify=False)
    resp.raise_for_status()
    return resp.json()


def download_lichtpunten_zuid(gebieden: list[str]) -> gpd.GeoDataFrame:
    where = where_clause(gebieden)
    count_payload = fetch_json(
        {
            "where": where,
            "returnCountOnly": "true",
            "f": "json",
        }
    )
    count = int(count_payload.get("count") or 0)
    print(f"Totaal lichtpunten op basis van filter: {count}")

    features: list[dict[str, Any]] = []
    total_batches = math.ceil(count / BATCH_SIZE) if count else 0

    for index in range(total_batches):
        offset = index * BATCH_SIZE
        batch_size = min(BATCH_SIZE, count - offset)
        print(f"Download batch {index + 1}/{total_batches} ({batch_size} features)")
        batch = fetch_json(
            {
                "where": where,
                "outFields": "LICHTPUNT_ID,LICHTPUNTTYPE,WOONPLAATS,WIJK,BUURT,STRAAT",
                "returnGeometry": "true",
                "outSR": "28992",
                "resultOffset": str(offset),
                "resultRecordCount": str(batch_size),
                "f": "geojson",
            }
        )
        features.extend(batch.get("features", []))

    if not features:
        return gpd.GeoDataFrame(columns=["LICHTPUNT_ID"], geometry=[], crs="EPSG:28992")

    gdf = gpd.GeoDataFrame.from_features(features)
    return enforce_rd_crs(gdf)


def add_scale_bar(ax, length_m=5_000):
    """Draw a simple metric scale bar in the lower-left corner."""
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 300, y0 + 300], color="#222222", linewidth=1.6)
    ax.plot([x1, x1], [y0 - 300, y0 + 300], color="#222222", linewidth=1.6)
    ax.text(
        (x0 + x1) / 2,
        y0 + 550,
        f"{length_m // 1000} km",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#222222",
    )


def main() -> None:
    gebieden = load_rd(DATA / "tir_gebieden.geojson")
    zuid = gebieden[gebieden["GEBDNAAM"].isin(ZUID_GEBIEDEN)].copy()
    zuid["geometry"] = zuid.geometry.make_valid()

    lichtpunten = download_lichtpunten_zuid(ZUID_GEBIEDEN)
    print(f"Gedownloade lichtpunten: {len(lichtpunten)}")

    # Veilige ruimtelijke check tegen de polygonen van Rotterdam Zuid.
    lichtpunten_zuid = gpd.sjoin(
        lichtpunten,
        zuid[["GEBDNAAM", "geometry"]],
        how="inner",
        predicate="within",
    )

    # Houd alleen originele kolommen + gebiedsnaam.
    keep_cols = [
        col
        for col in ["LICHTPUNT_ID", "LICHTPUNTTYPE", "WOONPLAATS", "WIJK", "BUURT", "STRAAT", "GEBDNAAM", "geometry"]
        if col in lichtpunten_zuid.columns
    ]
    lichtpunten_zuid = lichtpunten_zuid[keep_cols].copy()

    print(f"Lichtpunten na ruimtelijke filter: {len(lichtpunten_zuid)}")
    print("Per gebied:")
    print(lichtpunten_zuid.groupby("GEBDNAAM").size().sort_values(ascending=False).to_string())

    OUT.mkdir(exist_ok=True)
    geojson_out = OUT / "lichtpunten_rotterdam_zuid.geojson"
    lichtpunten_zuid.to_file(geojson_out, driver="GeoJSON")
    print(f"GeoJSON opgeslagen: {geojson_out}")

    fig, ax = plt.subplots(figsize=(14, 12))

    zuid.plot(
        ax=ax,
        color="#f6f3ee",
        edgecolor="#8c8377",
        linewidth=1.0,
        zorder=1,
    )
    lichtpunten_zuid.plot(
        ax=ax,
        color="#145DA0",
        markersize=1.7,
        alpha=0.75,
        zorder=2,
    )

    for _, row in zuid.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        centroid = row.geometry.representative_point()
        label = ax.text(
            centroid.x,
            centroid.y,
            row["GEBDNAAM"],
            ha="center",
            va="center",
            fontsize=9,
            color="#2f2a24",
            weight="bold",
            zorder=3,
        )
        label.set_path_effects([pe.withStroke(linewidth=2.5, foreground="white")])

    # geen schaalstok: afstand niet relevant (invariant 14)

    area_patch = mpatches.Patch(
        facecolor="#f6f3ee",
        edgecolor="#8c8377",
        label=f"Gebieden Rotterdam Zuid ({len(zuid)})",
    )
    licht_handle = mlines.Line2D(
        [],
        [],
        color="#145DA0",
        marker="o",
        linestyle="None",
        markersize=6,
        label=f"Lichtpunten ({len(lichtpunten_zuid):,})",
    )
    ax.legend(
        handles=[area_patch, licht_handle],
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="#d9d3cb",
    )

    from matplotlib.transforms import ScaledTranslation
    ax.set_title(
        "Alle lichtpunten in Rotterdam Zuid",
        fontsize=16,
        fontweight="bold",
        pad=28,
    )
    # subtitel: niet vet, kleiner dan de titel, net boven de kaart (titelhiërarchie)
    ax.text(
        0.5, 1.0, f"{len(lichtpunten_zuid):,} locaties in 8 gebieden",
        transform=ax.transAxes + ScaledTranslation(0, 7 / 72, fig.dpi_scale_trans),
        ha="center", va="bottom", fontsize=10.5, color="#555555",
    )
    ax.text(
        0.5,
        0.03,
        "Bron: Gemeente Rotterdam, SB_Infra/LICHTPUNTEN en TIR-gebieden",
        transform=fig.transFigure,
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )

    ax.set_axis_off()
    plt.tight_layout()

    png_out = OUT / "kaart_lichtpunten_rotterdam_zuid.png"
    fig.savefig(png_out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {png_out}")


if __name__ == "__main__":
    main()
