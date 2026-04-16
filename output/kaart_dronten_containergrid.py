"""Statische kaart: 100.000 containerwoningen ten zuiden van Dronten op OSM-ondergrond."""

from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import osmnx as ox
from shapely.geometry import box

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parent
OUT = PROJECT / "output"

PLACE = "Dronten, Flevoland, Netherlands"
UNITS = 100_000
CONTAINER_LENGTH = 12.2
CONTAINER_WIDTH = 2.44
FOOTPATH = 3.0
COLS = 400
ROWS = 250


def add_scale_bar(ax, length_m=1000):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.4, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 80, y0 + 80], color="#222222", linewidth=1.5)
    ax.plot([x1, x1], [y0 - 80, y0 + 80], color="#222222", linewidth=1.5)
    ax.text((x0 + x1) / 2, y0 + 160, "1 km", ha="center", va="bottom", fontsize=9, color="#222222")


def build_unit_grid(site_minx, site_miny):
    pitch_x = CONTAINER_WIDTH + FOOTPATH
    pitch_y = CONTAINER_LENGTH + FOOTPATH
    prototypes = []
    for row in range(ROWS):
        y0 = site_miny + row * pitch_y
        for col in range(COLS):
            x0 = site_minx + col * pitch_x
            prototypes.append(box(x0, y0, x0 + CONTAINER_WIDTH, y0 + CONTAINER_LENGTH))
    return gpd.GeoDataFrame({"geometry": prototypes}, crs="EPSG:28992")


def main():
    dronten = ox.geocode_to_gdf(PLACE).to_crs(epsg=28992)
    dronten_poly = dronten.geometry.iloc[0]

    minx, miny, maxx, maxy = dronten_poly.bounds
    pitch_x = CONTAINER_WIDTH + FOOTPATH
    pitch_y = CONTAINER_LENGTH + FOOTPATH
    site_width = COLS * CONTAINER_WIDTH + (COLS - 1) * FOOTPATH
    site_height = ROWS * CONTAINER_LENGTH + (ROWS - 1) * FOOTPATH

    # Plaats de grid direct ten zuiden van Dronten met beperkte marge.
    site_minx = (minx + maxx) / 2 - site_width / 2
    site_miny = miny - 600 - site_height
    site = box(site_minx, site_miny, site_minx + site_width, site_miny + site_height)

    units = build_unit_grid(site_minx, site_miny)
    site_gdf = gpd.GeoDataFrame({"geometry": [site]}, crs="EPSG:28992")

    fig, ax = plt.subplots(figsize=(15, 13))

    dronten.plot(ax=ax, color="#eef4fb", edgecolor="#3569b7", linewidth=1.2, zorder=1)
    dronten.boundary.plot(ax=ax, color="#3569b7", linewidth=1.6, zorder=2)

    site_gdf.plot(ax=ax, color="#fff3d6", edgecolor="#f2a900", linewidth=1.6, alpha=0.5, zorder=4)
    units.plot(ax=ax, color="#d94841", edgecolor="none", alpha=0.9, zorder=5)

    # Label Dronten en het nieuwe rastergebied.
    dronten_pt = dronten_poly.representative_point()
    ax.text(
        dronten_pt.x,
        dronten_pt.y,
        "Dronten",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#1f2f46",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.9),
        zorder=6,
    )
    ax.text(
        site.centroid.x,
        site.centroid.y,
        "100.000 containerwoningen\nperfect grid met 3 m voetpaden",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#7a1f19",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#e0d9cf", alpha=0.92),
        zorder=6,
    )

    add_scale_bar(ax)

    footprint_area = UNITS * CONTAINER_LENGTH * CONTAINER_WIDTH / 1_000_000
    gross_area = site.area / 1_000_000
    tech_text = "\n".join(
        [
            "Technisch",
            f"Grid: {COLS} x {ROWS} = {UNITS:,} woningen",
            f"Woningmaat: {CONTAINER_LENGTH:.1f} x {CONTAINER_WIDTH:.2f} m",
            f"Voetpad tussen woningen: {FOOTPATH:.1f} m",
            f"Rastermaat: {site_width/1000:.2f} x {site_height/1000:.2f} km",
            f"Bruto terrein: {gross_area:.2f} km2",
            f"Netto woon-footprint: {footprint_area:.2f} km2",
            "Ondergrond: OSM-boundary van Dronten",
        ]
    )
    ax.text(
        0.02,
        0.98,
        tech_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.3,
        color="#2f2a24",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#d9d3cb", alpha=0.97),
        zorder=7,
    )

    legend_handles = [
        mpatches.Patch(facecolor="#eef4fb", edgecolor="#3569b7", label="Dronten uit OSM"),
        mpatches.Patch(facecolor="#fff3d6", edgecolor="#f2a900", label="Plangebied"),
        mpatches.Patch(facecolor="#d94841", edgecolor="none", label="Containerwoningen"),
    ]
    ax.legend(
        handles=legend_handles,
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.96,
        facecolor="white",
        edgecolor="#d9d3cb",
    )

    expand = 1200
    ax.set_xlim(min(site.bounds[0], minx) - expand, max(site.bounds[2], maxx) + expand)
    ax.set_ylim(site.bounds[1] - expand, maxy + expand)
    ax.set_axis_off()
    ax.set_title(
        "100.000 containerwoningen ten zuiden van Dronten",
        fontsize=17,
        fontweight="bold",
        pad=16,
    )
    fig.text(
        0.5,
        0.03,
        "Conceptuele inpassing op OSM-ondergrond. De woningen staan in een exact orthogonaal raster met vaste tussenruimte voor voetpaden.",
        ha="center",
        fontsize=9.2,
        color="#5e5a55",
    )
    fig.subplots_adjust(left=0.03, right=0.99, top=0.93, bottom=0.08)

    OUT.mkdir(exist_ok=True)
    out = OUT / "kaart_dronten_100k_containerwoningen.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out}")
    print(tech_text)


if __name__ == "__main__":
    main()
