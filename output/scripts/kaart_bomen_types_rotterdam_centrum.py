"""Statische kaart: bomen in Rotterdam Centrum uitgesplitst naar type."""

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

TOP_N = 8
TYPE_COL = "BOOMSORTIMENT_NEDERLANDS"

# Rotterdam-style civic palette: warm red + municipal accents on a neutral base.
PALETTE = [
    "#d94841",  # red
    "#f2a900",  # yellow
    "#3569b7",  # blue
    "#007a78",  # teal
    "#e67e22",  # orange
    "#2d8a4e",  # green
    "#8c564b",  # brown
    "#5e5a55",  # dark neutral
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
        [gpd.read_file(path)[[TYPE_COL, "BOOMSORTIMENT", "geometry"]] for path in chunk_paths],
        ignore_index=True,
    )
    return gpd.GeoDataFrame(bomen, geometry="geometry", crs="EPSG:28992")


def add_scale_bar(ax, length_m=500):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.045
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 55, y0 + 55], color="#222222", linewidth=1.4)
    ax.plot([x1, x1], [y0 - 55, y0 + 55], color="#222222", linewidth=1.4)
    ax.text((x0 + x1) / 2, y0 + 120, f"{length_m} m", ha="center", va="bottom", fontsize=8.5, color="#222222")


def main():
    require_paths([DATA / "tir_gebieden.geojson", DATA / "bomen_chunks"])

    gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
    bomen = load_bomen()

    require_columns(gebieden, ["GEBDNAAM", "geometry"], "tir_gebieden")
    require_columns(bomen, [TYPE_COL, "BOOMSORTIMENT", "geometry"], "bomen")

    centrum = gebieden[gebieden["GEBDNAAM"] == "Rotterdam Centrum"][["GEBDNAAM", "geometry"]].copy()
    centrum["geometry"] = centrum.geometry.make_valid()

    bomen_centrum = gpd.sjoin(bomen, centrum, how="inner", predicate="within").copy()
    bomen_centrum["type_label"] = bomen_centrum[TYPE_COL].fillna("Onbekend")

    counts = bomen_centrum["type_label"].value_counts()
    top_types = counts.head(TOP_N).index.tolist()
    bomen_centrum["type_group"] = bomen_centrum["type_label"].where(
        bomen_centrum["type_label"].isin(top_types),
        "Overige typen",
    )
    grouped_counts = bomen_centrum["type_group"].value_counts()

    color_map = {name: PALETTE[idx] for idx, name in enumerate(top_types)}
    color_map["Overige typen"] = OTHER_COLOR

    print(f"Totaal bomen in Rotterdam Centrum: {len(bomen_centrum)}")
    print(grouped_counts.to_string())

    fig = plt.figure(figsize=(16, 11))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.25, 1], wspace=0.08)
    ax_map = fig.add_subplot(gs[0, 0])
    ax_bar = fig.add_subplot(gs[0, 1])

    centrum.plot(ax=ax_map, color=POLYGON_FILL, edgecolor=POLYGON_EDGE, linewidth=1.1, zorder=1)

    for name in top_types + ["Overige typen"]:
        subset = bomen_centrum[bomen_centrum["type_group"] == name]
        if subset.empty:
            continue
        subset.plot(
            ax=ax_map,
            color=color_map[name],
            markersize=4.2 if name != "Overige typen" else 2.8,
            alpha=0.82 if name != "Overige typen" else 0.45,
            zorder=2 if name == "Overige typen" else 3,
        )

    add_scale_bar(ax_map)
    ax_map.text(
        0.02,
        0.98,
        "\n".join(
            [
                "Key specs",
                f"Totaal bomen: {len(bomen_centrum):,}",
                f"Unieke typen: {counts.size}",
                f"Grootste type: {top_types[0]} ({int(counts.iloc[0]):,})",
                "Gebiedsdefinitie: TIR-gebied Rotterdam Centrum",
            ]
        ),
        transform=ax_map.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#2f2a24",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#d9d3cb", alpha=0.96),
        zorder=4,
    )
    ax_map.set_axis_off()
    ax_map.set_title(
        "Bomen per type in Rotterdam Centrum",
        fontsize=16,
        fontweight="bold",
        pad=14,
    )

    bar_series = grouped_counts.reindex(top_types + ["Overige typen"]).fillna(0)
    bar_colors = [color_map[name] for name in bar_series.index]
    ax_bar.barh(bar_series.index[::-1], bar_series.values[::-1], color=bar_colors[::-1], edgecolor="none")
    ax_bar.set_title("Top boomtypen", fontsize=13, fontweight="bold", pad=10)
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
        ax_bar.text(value + 18, idx, f"{int(value):,}", va="center", fontsize=8.8, color="#2f2a24")

    legend_handles = [
        mpatches.Patch(facecolor=POLYGON_FILL, edgecolor=POLYGON_EDGE, label="Gebied Rotterdam Centrum")
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
        fontsize=8.8,
        title_fontsize=9.5,
    )

    fig.text(
        0.5,
        0.03,
        "Bron: Gemeente Rotterdam bomenbestand en TIR-gebieden. Kleuren: Rotterdam GeoAI civic palette.",
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )
    fig.subplots_adjust(left=0.04, right=0.98, top=0.92, bottom=0.08, wspace=0.08)

    OUT.mkdir(exist_ok=True)
    out = OUT / "kaart_bomen_types_rotterdam_centrum.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
