"""Vergelijking afvalbakken: Rotterdam Centrum vs Hillegersberg-Schiebroek."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "General data" / "Data"
OUT = PROJECT / "output"

A = "Rotterdam Centrum"
B = "Hillegersberg-Schiebroek"


def load_rotterdam(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def add_scale_bar(ax, length_m=5000):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222", linewidth=2.2)
    ax.plot([x0, x0], [y0 - 220, y0 + 220], color="#222", linewidth=1.5)
    ax.plot([x1, x1], [y0 - 220, y0 + 220], color="#222", linewidth=1.5)
    ax.text((x0 + x1) / 2, y0 + 430, "5 km", ha="center", va="bottom", fontsize=9)


def main() -> None:
    OUT.mkdir(exist_ok=True)

    gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
    afval = load_rotterdam(DATA / "afvalbak.geojson")

    gebieden = gebieden[["GEBDNAAM", "geometry"]].copy()
    gebieden["geometry"] = gebieden.geometry.make_valid()

    afval_join = gpd.sjoin(afval, gebieden, how="inner", predicate="within")
    counts = afval_join.groupby("GEBDNAAM").size().sort_values(ascending=False)

    count_a = int(counts.get(A, 0))
    count_b = int(counts.get(B, 0))

    print(f"{A}: {count_a}")
    print(f"{B}: {count_b}")
    if count_b > 0:
        print(f"Verhouding {A}/{B}: {count_a / count_b:.2f}")

    map_data = afval_join.copy()
    map_data["cat"] = "Overige gebieden"
    map_data.loc[map_data["GEBDNAAM"] == A, "cat"] = A
    map_data.loc[map_data["GEBDNAAM"] == B, "cat"] = B

    fig, (ax_map, ax_bar) = plt.subplots(
        1, 2, figsize=(16, 9), gridspec_kw={"width_ratios": [1.9, 1.0]}
    )

    gebieden.plot(ax=ax_map, color="#f2efe9", edgecolor="#a39a8d", linewidth=0.8, zorder=1)

    map_data[map_data["cat"] == "Overige gebieden"].plot(
        ax=ax_map, color="#9aa3ad", markersize=1.2, alpha=0.25, zorder=2
    )
    map_data[map_data["cat"] == B].plot(
        ax=ax_map, color="#2b8cbe", markersize=4.0, alpha=0.85, zorder=3
    )
    map_data[map_data["cat"] == A].plot(
        ax=ax_map, color="#e34a33", markersize=4.0, alpha=0.85, zorder=4
    )

    highlight = gebieden[gebieden["GEBDNAAM"].isin([A, B])]
    highlight.plot(ax=ax_map, facecolor="none", edgecolor="#1f1f1f", linewidth=1.8, zorder=5)

    # geen schaalstok: afstand niet relevant (invariant 14)

    legend_handles = [
        mpatches.Patch(facecolor="#f2efe9", edgecolor="#a39a8d", label="Gebieden Rotterdam"),
        mlines.Line2D([], [], color="#e34a33", marker="o", linestyle="None", markersize=7, label=f"{A} ({count_a})"),
        mlines.Line2D([], [], color="#2b8cbe", marker="o", linestyle="None", markersize=7, label=f"{B} ({count_b})"),
        mlines.Line2D([], [], color="#9aa3ad", marker="o", linestyle="None", markersize=6, alpha=0.5, label="Overige afvalbakken"),
    ]
    ax_map.legend(handles=legend_handles, title="Legenda", loc="lower right", frameon=True)
    ax_map.set_title("Afvalbakken binnen gemeente Rotterdam", fontsize=13, fontweight="bold")
    # subtitel deelkaart: niet vet, kleiner dan de titel (titelhiërarchie)
    ax_map.text(0.5, 1.0, "met focus op 2 gebieden", transform=ax_map.transAxes,
                ha="center", va="top", fontsize=9.5, color="#555555")
    ax_map.set_axis_off()

    labels = [A, B]
    vals = [count_a, count_b]
    colors = ["#e34a33", "#2b8cbe"]
    bars = ax_bar.bar(labels, vals, color=colors, width=0.6)
    ax_bar.set_title("Vergelijking aantallen", fontsize=13, fontweight="bold")
    ax_bar.set_ylabel("Aantal afvalbakken")
    ax_bar.grid(axis="y", alpha=0.25)
    ax_bar.set_axisbelow(True)
    for bar, v in zip(bars, vals):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.02, f"{v}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    fig.suptitle("Gemeente Rotterdam: afvalbakkenvergelijking Rotterdam Centrum vs Hillegersberg-Schiebroek", fontsize=15, fontweight="bold", y=0.98)
    fig.text(0.5, 0.015, "Bron: Gemeente Rotterdam SB_Infra/Afvalbak + TIR gebieden | CRS: EPSG:28992", ha="center", fontsize=9, color="#555")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    out_png = OUT / "kaart_afvalbakken_vergelijking_centrum_hillegersberg.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Kaart opgeslagen: {out_png}")


if __name__ == "__main__":
    main()
