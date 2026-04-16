"""Statische kaart: afvalbakken in Rotterdam Zuid."""

from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA = Path("General data/Data")
OUT = Path("output")

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


def load_rotterdam(path: Path) -> gpd.GeoDataFrame:
    """Load Rotterdam GeoJSON and coerce to RD New when metadata is wrong."""
    gdf = gpd.read_file(path)
    minx, miny, maxx, maxy = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def add_scale_bar(ax, length_m=2_000):
    """Draw a simple metric scale bar in the lower-left corner."""
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 160, y0 + 160], color="#222222", linewidth=1.6)
    ax.plot([x1, x1], [y0 - 160, y0 + 160], color="#222222", linewidth=1.6)
    ax.text(
        (x0 + x1) / 2,
        y0 + 350,
        f"{length_m // 1000} km",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#222222",
    )


def main():
    gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
    afval = load_rotterdam(DATA / "afvalbak.geojson")

    zuid = gebieden[gebieden["GEBDNAAM"].isin(ZUID_GEBIEDEN)].copy()
    zuid["geometry"] = zuid.geometry.make_valid()

    afval_zuid = gpd.sjoin(
        afval,
        zuid[["GEBDNAAM", "geometry"]],
        how="inner",
        predicate="within",
    )

    print(f"Afvalbakken in Rotterdam Zuid: {len(afval_zuid)}")
    print(afval_zuid.groupby("GEBDNAAM").size().sort_values(ascending=False).to_string())

    fig, ax = plt.subplots(figsize=(14, 12))

    zuid.plot(
        ax=ax,
        color="#f6f3ee",
        edgecolor="#8c8377",
        linewidth=1.0,
        zorder=1,
    )
    afval_zuid.plot(
        ax=ax,
        color="#d94841",
        markersize=3.2,
        alpha=0.72,
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

    add_scale_bar(ax)

    area_patch = mpatches.Patch(
        facecolor="#f6f3ee",
        edgecolor="#8c8377",
        label=f"Gebieden Rotterdam Zuid ({len(zuid)})",
    )
    afval_handle = mlines.Line2D(
        [],
        [],
        color="#d94841",
        marker="o",
        linestyle="None",
        markersize=6,
        label=f"Afvalbakken ({len(afval_zuid)})",
    )
    ax.legend(
        handles=[area_patch, afval_handle],
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="#d9d3cb",
    )

    ax.set_title(
        f"Afvalbakken in Rotterdam Zuid\n{len(afval_zuid):,} locaties in 8 gebieden",
        fontsize=16,
        fontweight="bold",
        pad=18,
    )
    ax.text(
        0.5,
        0.03,
        "Bron: Gemeente Rotterdam, SB_Infra/Afvalbak en TIR-gebieden",
        transform=fig.transFigure,
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )
    ax.set_axis_off()
    plt.tight_layout()

    OUT.mkdir(exist_ok=True)
    out = OUT / "kaart_afvalbakken_rotterdam_zuid.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
