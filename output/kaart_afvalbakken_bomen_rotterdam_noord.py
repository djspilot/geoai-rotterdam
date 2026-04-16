"""Statische kaart: afvalbakken en bomen in Rotterdam Noord."""

from glob import glob
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "General data/Data"
OUT = PROJECT / "output"

# Stedelijke gebieden ten noorden van de Maas.
NOORD_GEBIEDEN = [
    "Delfshaven",
    "Hillegersberg-Schiebroek",
    "Kralingen-Crooswijk",
    "Nieuw Mathenesse",
    "Noord",
    "Overschie",
    "Prins Alexander",
    "Rivium",
    "Rotterdam Centrum",
    "Rotterdam-Noord-West",
    "Spaanse Polder",
]


def load_rotterdam(path: Path) -> gpd.GeoDataFrame:
    """Load Rotterdam GeoJSON and coerce to RD New when metadata is wrong."""
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def load_bomen() -> gpd.GeoDataFrame:
    chunks = sorted(glob(str(DATA / "bomen_chunks/*.geojson")))
    bomen = pd.concat([gpd.read_file(path) for path in chunks], ignore_index=True)
    return gpd.GeoDataFrame(bomen, geometry="geometry", crs="EPSG:28992")


def add_scale_bar(ax, length_m=2_000):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 160, y0 + 160], color="#222222", linewidth=1.6)
    ax.plot([x1, x1], [y0 - 160, y0 + 160], color="#222222", linewidth=1.6)
    ax.text((x0 + x1) / 2, y0 + 350, f"{length_m // 1000} km", ha="center", va="bottom", fontsize=9, color="#222222")


def format_specs(afval_noord, bomen_noord, noord):
    afval_per_gebied = afval_noord.groupby("GEBDNAAM").size().sort_values(ascending=False)
    bomen_per_gebied = bomen_noord.groupby("GEBDNAAM").size().sort_values(ascending=False)
    spec_lines = [
        "Key specs",
        f"Gebieden: {len(noord)}",
        f"Afvalbakken: {len(afval_noord):,}",
        f"Bomen: {len(bomen_noord):,}",
        f"Meeste afvalbakken: {afval_per_gebied.index[0]} ({int(afval_per_gebied.iloc[0]):,})",
        f"Meeste bomen: {bomen_per_gebied.index[0]} ({int(bomen_per_gebied.iloc[0]):,})",
    ]
    return "\n".join(spec_lines)


def main():
    gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
    afval = load_rotterdam(DATA / "afvalbak.geojson")
    bomen = load_bomen()

    noord = gebieden[gebieden["GEBDNAAM"].isin(NOORD_GEBIEDEN)].copy()
    noord["geometry"] = noord.geometry.make_valid()

    afval_noord = gpd.sjoin(
        afval,
        noord[["GEBDNAAM", "geometry"]],
        how="inner",
        predicate="within",
    )
    bomen_noord = gpd.sjoin(
        bomen,
        noord[["GEBDNAAM", "geometry"]],
        how="inner",
        predicate="within",
    )

    print(f"Afvalbakken in Rotterdam Noord: {len(afval_noord)}")
    print(f"Bomen in Rotterdam Noord: {len(bomen_noord)}")
    print("Top 5 gebieden afvalbakken:")
    print(afval_noord.groupby("GEBDNAAM").size().sort_values(ascending=False).head().to_string())
    print("Top 5 gebieden bomen:")
    print(bomen_noord.groupby("GEBDNAAM").size().sort_values(ascending=False).head().to_string())

    fig, ax = plt.subplots(figsize=(15, 12))

    noord.plot(
        ax=ax,
        color="#f6f3ee",
        edgecolor="#8c8377",
        linewidth=1.0,
        zorder=1,
    )
    bomen_noord.plot(
        ax=ax,
        color="#2d8a4e",
        markersize=0.35,
        alpha=0.42,
        zorder=2,
    )
    afval_noord.plot(
        ax=ax,
        color="#d94841",
        markersize=3.2,
        alpha=0.72,
        zorder=3,
    )

    for _, row in noord.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        point = row.geometry.representative_point()
        label = ax.text(
            point.x,
            point.y,
            row["GEBDNAAM"],
            ha="center",
            va="center",
            fontsize=8.8,
            color="#2f2a24",
            weight="bold",
            zorder=4,
        )
        label.set_path_effects([pe.withStroke(linewidth=2.5, foreground="white")])

    specs = format_specs(afval_noord, bomen_noord, noord)
    ax.text(
        0.02,
        0.98,
        specs,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#2f2a24",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#d9d3cb", alpha=0.96),
        zorder=5,
    )

    add_scale_bar(ax)

    area_patch = mpatches.Patch(
        facecolor="#f6f3ee",
        edgecolor="#8c8377",
        label=f"Gebieden Rotterdam Noord ({len(noord)})",
    )
    bomen_handle = mlines.Line2D(
        [],
        [],
        color="#2d8a4e",
        marker="o",
        linestyle="None",
        markersize=4,
        label=f"Bomen ({len(bomen_noord):,})",
    )
    afval_handle = mlines.Line2D(
        [],
        [],
        color="#d94841",
        marker="o",
        linestyle="None",
        markersize=6,
        label=f"Afvalbakken ({len(afval_noord):,})",
    )
    ax.legend(
        handles=[area_patch, bomen_handle, afval_handle],
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="#d9d3cb",
    )

    ax.set_title(
        "Afvalbakken en bomen in Rotterdam Noord\nStedelijke gebieden ten noorden van de Maas",
        fontsize=16,
        fontweight="bold",
        pad=18,
    )
    ax.text(
        0.5,
        0.03,
        "Bron: Gemeente Rotterdam, SB_Infra/Afvalbak, bomenbestand en TIR-gebieden",
        transform=fig.transFigure,
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )
    ax.set_axis_off()
    plt.tight_layout()

    OUT.mkdir(exist_ok=True)
    out = OUT / "kaart_afvalbakken_bomen_rotterdam_noord.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
