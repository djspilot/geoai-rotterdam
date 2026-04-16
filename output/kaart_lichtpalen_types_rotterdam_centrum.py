"""Statische kaart: lichtpunten per type in Stadsdriehoek (Rotterdam Centrum)."""

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

TYPE_COL = "LICHTPUNTTYPE"

PALETTE = [
    "#d94841",
    "#f2a900",
    "#3569b7",
    "#007a78",
    "#e67e22",
    "#2d8a4e",
    "#8c564b",
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


def top_n_with_other(series, n=7, other_label="Overige typen"):
    counts = series.fillna("Onbekend").astype(str).value_counts()
    top = counts.head(n).index.tolist()
    grouped = series.fillna("Onbekend").astype(str).where(lambda s: s.isin(top), other_label)
    return grouped, counts, top


def add_scale_bar(ax, length_m=250):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.045
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 22, y0 + 22], color="#222222", linewidth=1.4)
    ax.plot([x1, x1], [y0 - 22, y0 + 22], color="#222222", linewidth=1.4)
    ax.text((x0 + x1) / 2, y0 + 42, f"{length_m} m", ha="center", va="bottom", fontsize=8.5, color="#222222")


def main():
    require_paths([DATA / "tir_gebieden.geojson", DATA / "lichtpunten_stadsdriehoek.geojson"])

    gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
    licht = load_rotterdam(DATA / "lichtpunten_stadsdriehoek.geojson")

    require_columns(gebieden, ["GEBDNAAM", "geometry"], "tir_gebieden")
    require_columns(licht, [TYPE_COL, "WIJK", "BUURT", "geometry"], "lichtpunten")

    centrum = gebieden[gebieden["GEBDNAAM"] == "Rotterdam Centrum"][["GEBDNAAM", "geometry"]].copy()
    centrum["geometry"] = centrum.geometry.make_valid()

    licht = licht.copy()
    licht["type_group"], counts, top_types = top_n_with_other(licht[TYPE_COL], n=7)
    grouped_counts = licht["type_group"].value_counts()

    print("Lokale dekking: alleen Stadsdriehoek binnen Rotterdam Centrum")
    print(f"Totaal lichtpunten: {len(licht)}")
    print(grouped_counts.to_string())

    color_map = {name: PALETTE[idx] for idx, name in enumerate(top_types)}
    color_map["Overige typen"] = OTHER_COLOR

    fig = plt.figure(figsize=(16, 11))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.2, 1], wspace=0.08)
    ax_map = fig.add_subplot(gs[0, 0])
    ax_bar = fig.add_subplot(gs[0, 1])

    centrum.plot(ax=ax_map, color=POLYGON_FILL, edgecolor=POLYGON_EDGE, linewidth=1.1, zorder=1)

    for name in top_types + ["Overige typen"]:
        subset = licht[licht["type_group"] == name]
        if subset.empty:
            continue
        subset.plot(
            ax=ax_map,
            color=color_map[name],
            markersize=8.0 if name != "Overige typen" else 5.5,
            alpha=0.9 if name != "Overige typen" else 0.5,
            zorder=3 if name != "Overige typen" else 2,
        )

    add_scale_bar(ax_map)
    ax_map.text(
        0.02,
        0.98,
        "\n".join(
            [
                "Key specs",
                f"Totaal lichtpunten: {len(licht):,}",
                f"Unieke typen: {counts.size}",
                f"Grootste type: {top_types[0]} ({int(counts.iloc[0]):,})",
                "Dekking: Stadsdriehoek",
                "Context: deel van Rotterdam Centrum",
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
        "Lichtpunten per type in Stadsdriehoek\n(deel van Rotterdam Centrum)",
        fontsize=16,
        fontweight="bold",
        pad=14,
    )

    bar_series = grouped_counts.reindex(top_types + ["Overige typen"]).fillna(0)
    bar_colors = [color_map[name] for name in bar_series.index]
    ax_bar.barh(bar_series.index[::-1], bar_series.values[::-1], color=bar_colors[::-1], edgecolor="none")
    ax_bar.set_title("Top lichtpunttypen", fontsize=13, fontweight="bold", pad=10)
    ax_bar.tick_params(axis="y", labelsize=9)
    ax_bar.tick_params(axis="x", labelsize=9)
    ax_bar.grid(axis="x", color="#e6e1da", linewidth=0.8)
    ax_bar.set_axisbelow(True)
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.spines["left"].set_color("#d9d3cb")
    ax_bar.spines["bottom"].set_color("#d9d3cb")
    ax_bar.set_xlabel("Aantal lichtpunten", fontsize=10)
    for idx, value in enumerate(bar_series.values[::-1]):
        ax_bar.text(value + 12, idx, f"{int(value):,}", va="center", fontsize=8.8, color="#2f2a24")

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
        "Bron: Gemeente Rotterdam lichtpuntenbestand (lokale extractie Stadsdriehoek) en TIR-gebieden.",
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )
    fig.subplots_adjust(left=0.04, right=0.98, top=0.92, bottom=0.08, wspace=0.08)

    OUT.mkdir(exist_ok=True)
    out = OUT / "kaart_lichtpalen_types_rotterdam_centrum.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
