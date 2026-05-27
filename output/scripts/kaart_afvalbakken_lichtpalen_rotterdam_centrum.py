"""Statische kaart: afvalbakken en lichtpalen in Rotterdam Centrum."""

from __future__ import annotations

import sys

sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")

import geopandas as gpd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from rotterdam import (
    ARCGIS_LAYERS,
    ASSET_COLORS,
    STYLE,
    fetch_arcgis_layer,
    finalize_map,
    load_layer,
    save_map,
    setup_headless_matplotlib,
    style_map,
    validate_map,
)

setup_headless_matplotlib()
import matplotlib.pyplot as plt

CENTRUM = "Rotterdam Centrum"


def spatial_filter(points: gpd.GeoDataFrame, polygon: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return gpd.sjoin(points, polygon[["geometry"]], how="inner", predicate="within").drop(
        columns="index_right"
    )


def main() -> None:
    gebieden = load_layer("gebieden")
    centrum = gebieden[gebieden["GEBDNAAM"] == CENTRUM].copy()
    centrum["geometry"] = centrum.geometry.make_valid()
    if centrum.empty:
        raise ValueError(f"Gebied '{CENTRUM}' niet gevonden in tir_gebieden")

    # Afvalbakken: attribuutfilter + ruimtelijke verificatie
    afval = load_layer("afvalbak")
    afval_centrum = spatial_filter(afval[afval["WOONPLAATS"] == CENTRUM], centrum)
    print(f"Afvalbakken in Rotterdam Centrum: {len(afval_centrum):,}")

    # Lichtpalen: live fetch via ArcGIS REST (geen lokale dump van heel Centrum)
    licht_fc = fetch_arcgis_layer(
        ARCGIS_LAYERS["lichtpunten"],
        where="WOONPLAATS='Rotterdam Centrum'",
    )
    licht = gpd.GeoDataFrame.from_features(licht_fc["features"], crs="EPSG:28992")
    licht_centrum = spatial_filter(licht, centrum)
    print(f"Lichtpalen in Rotterdam Centrum: {len(licht_centrum):,}")

    # Kaart
    fig, ax = plt.subplots(figsize=(13, 12))
    centrum.plot(
        ax=ax,
        facecolor=STYLE["polygon_fill"],
        edgecolor=STYLE["boundary_color"],
        linewidth=1.0,
        zorder=1,
    )
    licht_centrum.plot(
        ax=ax,
        color=ASSET_COLORS["lichtpunten"],
        markersize=4.0,
        alpha=0.65,
        zorder=2,
    )
    afval_centrum.plot(
        ax=ax,
        color=ASSET_COLORS["afvalbak"],
        markersize=6.0,
        alpha=0.85,
        zorder=3,
    )

    style_map(ax, title=f"Afvalbakken en lichtpalen in {CENTRUM}")

    area_patch = mpatches.Patch(
        facecolor=STYLE["polygon_fill"],
        edgecolor=STYLE["boundary_color"],
        label=f"Gebied {CENTRUM}",
    )
    licht_handle = mlines.Line2D(
        [], [], color=ASSET_COLORS["lichtpunten"], marker="o", linestyle="None",
        markersize=6, label=f"Lichtpalen (n={len(licht_centrum):,})",
    )
    afval_handle = mlines.Line2D(
        [], [], color=ASSET_COLORS["afvalbak"], marker="o", linestyle="None",
        markersize=7, label=f"Afvalbakken (n={len(afval_centrum):,})",
    )
    ax.legend(
        handles=[area_patch, afval_handle, licht_handle],
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.96,
        facecolor="white",
        edgecolor=STYLE["separator_color"],
        fontsize=9,
    )

    finalize_map(
        fig,
        source="Obsurv via diensten.rotterdam.nl (Afvalbak, LICHTPUNTEN) + TIR-gebieden",
    )
    for w in validate_map(fig, ax, data=afval_centrum):
        print(f"WARN: {w}")

    out = save_map(fig, "kaart_afvalbakken_lichtpalen_rotterdam_centrum")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
