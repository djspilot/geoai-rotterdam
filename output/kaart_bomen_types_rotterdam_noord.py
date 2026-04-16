"""Statische kaart: alle bomen in Rotterdam Noord + overzicht per type."""

from glob import glob
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "General data/Data"
OUT = PROJECT / "output"

TYPE_COL = "BOOMSORTIMENT_NEDERLANDS"
TOP_N = 10

ROTTERDAM_NOORD_GEBIEDEN = [
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

PALETTE = [
    "#d94841",
    "#f2a900",
    "#3569b7",
    "#007a78",
    "#e67e22",
    "#2d8a4e",
    "#8c564b",
    "#5e5a55",
    "#5b8ff9",
    "#9a6bcd",
]
OTHER_COLOR = "#b7b1a7"
POLYGON_FILL = "#f6f3ee"
POLYGON_EDGE = "#8c8377"


def require_paths(paths):
    missing = [str(path) for path in paths if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Ontbrekende databronnen: {missing}")


def require_columns(gdf, columns, name):
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise KeyError(f"{name} mist kolommen: {missing}")


def load_rotterdam(path):
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def load_bomen():
    chunk_paths = sorted(glob(str(DATA / "bomen_chunks/*.geojson")))
    if not chunk_paths:
        raise FileNotFoundError("Geen bomen-chunks gevonden in data map")
    bomen = pd.concat(
        [gpd.read_file(path)[[TYPE_COL, "geometry"]] for path in chunk_paths],
        ignore_index=True,
    )
    return gpd.GeoDataFrame(bomen, geometry="geometry", crs="EPSG:28992")


def add_scale_bar(ax, length_m=3_000):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 220, y0 + 220], color="#222222", linewidth=1.4)
    ax.plot([x1, x1], [y0 - 220, y0 + 220], color="#222222", linewidth=1.4)
    ax.text((x0 + x1) / 2, y0 + 450, f"{length_m // 1000} km", ha="center", va="bottom", fontsize=8.8, color="#222222")


def main():
    require_paths([DATA / "tir_gebieden.geojson", DATA / "bomen_chunks"])

    gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
    bomen = load_bomen()

    require_columns(gebieden, ["GEBDNAAM", "geometry"], "tir_gebieden")
    require_columns(bomen, [TYPE_COL, "geometry"], "bomen")

    noord = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_NOORD_GEBIEDEN)][["GEBDNAAM", "geometry"]].copy()
    noord["geometry"] = noord.geometry.make_valid()

    bomen_noord = gpd.sjoin(bomen, noord, how="inner", predicate="within").copy()
    bomen_noord["type_label"] = bomen_noord[TYPE_COL].fillna("Waarde onbekend")

    counts = bomen_noord["type_label"].value_counts()
    top_types = counts.head(TOP_N).index.tolist()
    bomen_noord["type_group"] = bomen_noord["type_label"].where(
        bomen_noord["type_label"].isin(top_types),
        "Overige typen",
    )
    grouped_counts = bomen_noord["type_group"].value_counts()

    color_map = {name: PALETTE[idx] for idx, name in enumerate(top_types)}
    color_map["Overige typen"] = OTHER_COLOR

    print(f"Totaal bomen in Rotterdam Noord: {len(bomen_noord):,}")
    print(grouped_counts.to_string())

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.2, 1], wspace=0.08)
    ax_map = fig.add_subplot(gs[0, 0])
    ax_bar = fig.add_subplot(gs[0, 1])

    noord.plot(ax=ax_map, color=POLYGON_FILL, edgecolor=POLYGON_EDGE, linewidth=0.95, zorder=1)

    for name in top_types + ["Overige typen"]:
        subset = bomen_noord[bomen_noord["type_group"] == name]
        if subset.empty:
            continue
        subset.plot(
            ax=ax_map,
            color=color_map[name],
            markersize=0.32 if name != "Overige typen" else 0.26,
            alpha=0.45 if name != "Overige typen" else 0.24,
            zorder=2 if name == "Overige typen" else 3,
        )

    add_scale_bar(ax_map)
    ax_map.text(
        0.02,
        0.98,
        "\n".join(
            [
                "Key specs",
                f"Totaal bomen: {len(bomen_noord):,}",
                f"Unieke typen: {counts.size}",
                f"Top type: {top_types[0]} ({int(counts.iloc[0]):,})",
                "Gebiedsdefinitie: TIR-gebieden Rotterdam Noord (11 gebieden)",
            ]
        ),
        transform=ax_map.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#2f2a24",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#d9d3cb", alpha=0.96),
        zorder=5,
    )
    ax_map.set_axis_off()
    ax_map.set_title("Alle bomen in Rotterdam Noord, per type", fontsize=16, fontweight="bold", pad=14)

    bar_series = grouped_counts.reindex(top_types + ["Overige typen"]).fillna(0)
    bar_colors = [color_map[name] for name in bar_series.index]
    ax_bar.barh(bar_series.index[::-1], bar_series.values[::-1], color=bar_colors[::-1], edgecolor="none")
    ax_bar.set_title("Overzicht per type", fontsize=13, fontweight="bold", pad=10)
    ax_bar.tick_params(axis="y", labelsize=9)
    ax_bar.tick_params(axis="x", labelsize=9)
    ax_bar.grid(axis="x", color="#e6e1da", linewidth=0.8)
    ax_bar.set_axisbelow(True)
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.spines["left"].set_color("#d9d3cb")
    ax_bar.spines["bottom"].set_color("#d9d3cb")
    ax_bar.set_xlabel("Aantal bomen", fontsize=10)
    for idx, value in enumerate(bar_series.values[::-1]):
        ax_bar.text(value + 120, idx, f"{int(value):,}", va="center", fontsize=8.6, color="#2f2a24")

    legend_handles = [
        mpatches.Patch(facecolor=POLYGON_FILL, edgecolor=POLYGON_EDGE, label="Gebieden Rotterdam Noord"),
    ]
    legend_handles.extend(
        [
            mlines.Line2D([], [], color=color_map[name], marker="o", linestyle="None", markersize=6, label=name)
            for name in top_types
        ]
    )
    legend_handles.append(
        mlines.Line2D([], [], color=OTHER_COLOR, marker="o", linestyle="None", markersize=6, label="Overige typen")
    )
    ax_map.legend(
        handles=legend_handles,
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.96,
        facecolor="white",
        edgecolor="#d9d3cb",
        fontsize=8.4,
        title_fontsize=9.2,
    )

    fig.text(
        0.5,
        0.03,
        "Bron: Gemeente Rotterdam bomenbestand (SB_Infra/Bomen) en TIR-gebieden. Projectie: EPSG:28992.",
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )
    fig.subplots_adjust(left=0.04, right=0.98, top=0.92, bottom=0.08, wspace=0.08)

    OUT.mkdir(exist_ok=True)
    out = OUT / "kaart_bomen_types_rotterdam_noord.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
