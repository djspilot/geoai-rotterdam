"""Statische kaart: afvalbakken en bomen in Rotterdam Centrum."""

from __future__ import annotations

from glob import glob
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "General data" / "Data"
OUT = PROJECT / "output"
CENTRUM_GEBIED = "Rotterdam Centrum"


def load_rotterdam(path: Path) -> gpd.GeoDataFrame:
    """Load Rotterdam GeoJSON and coerce to RD New when metadata is wrong."""
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def require_paths(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Ontbrekende databronnen: {missing}")


def require_columns(gdf: gpd.GeoDataFrame, columns: list[str], name: str) -> None:
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise KeyError(f"{name} mist kolommen: {missing}")


def load_bomen_centrum() -> gpd.GeoDataFrame:
    """Load only bomen records for Rotterdam Centrum from chunked data."""
    chunk_paths = sorted(glob(str(DATA / "bomen_chunks" / "*.geojson")))
    if not chunk_paths:
        raise FileNotFoundError("Geen bomen chunks gevonden onder General data/Data/bomen_chunks")

    selected: list[gpd.GeoDataFrame] = []
    for chunk_path in chunk_paths:
        gdf = load_rotterdam(Path(chunk_path))
        require_columns(gdf, ["WOONPLAATS", "geometry"], f"bomen chunk {Path(chunk_path).name}")
        sub = gdf[gdf["WOONPLAATS"] == CENTRUM_GEBIED]
        if not sub.empty:
            selected.append(sub)

    if not selected:
        return gpd.GeoDataFrame(columns=["WOONPLAATS"], geometry=[], crs="EPSG:28992")

    merged = pd.concat(selected, ignore_index=True)
    return gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:28992")


def add_scale_bar(ax, length_m=1_000):
    """Draw a simple metric scale bar in the lower-left corner."""
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222222", linewidth=2.2, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 70, y0 + 70], color="#222222", linewidth=1.6)
    ax.plot([x1, x1], [y0 - 70, y0 + 70], color="#222222", linewidth=1.6)
    ax.text((x0 + x1) / 2, y0 + 150, f"{length_m // 1000 if length_m >= 1000 else length_m} {'km' if length_m >= 1000 else 'm'}", ha="center", va="bottom", fontsize=9, color="#222222")


def main() -> None:
    gebieden_path = DATA / "tir_gebieden.geojson"
    afval_path = DATA / "afvalbak.geojson"
    require_paths([gebieden_path, afval_path])

    gebieden = load_rotterdam(gebieden_path)
    afval = load_rotterdam(afval_path)
    bomen_centrum_attr = load_bomen_centrum()

    require_columns(gebieden, ["GEBDNAAM", "geometry"], "tir_gebieden")
    require_columns(afval, ["WOONPLAATS", "geometry"], "afvalbak")

    centrum = gebieden[gebieden["GEBDNAAM"] == CENTRUM_GEBIED].copy()
    if centrum.empty:
        raise ValueError("Gebied 'Rotterdam Centrum' niet gevonden in tir_gebieden")
    centrum["geometry"] = centrum.geometry.make_valid()

    # Stap 1: attribuutfilter (snel) op woonplaats.
    afval_attr = afval[afval["WOONPLAATS"] == CENTRUM_GEBIED].copy()
    print(f"Afvalbakken op attribuutfilter WOONPLAATS: {len(afval_attr)}")
    print(f"Bomen op attribuutfilter WOONPLAATS: {len(bomen_centrum_attr)}")

    # Stap 2: ruimtelijke verificatie op TIR-gebiedpolygonen.
    afval_centrum = gpd.sjoin(
        afval_attr,
        centrum[["GEBDNAAM", "geometry"]],
        how="inner",
        predicate="within",
    )
    bomen_centrum = gpd.sjoin(
        bomen_centrum_attr,
        centrum[["GEBDNAAM", "geometry"]],
        how="inner",
        predicate="within",
    )

    afval_cols = [col for col in ["TYPE", "WOONPLAATS", "WIJK", "GEBDNAAM", "geometry"] if col in afval_centrum.columns]
    boom_cols = [col for col in ["BOOMSORTIMENT_NEDERLANDS", "WOONPLAATS", "WIJK", "GEBDNAAM", "geometry"] if col in bomen_centrum.columns]
    afval_centrum = afval_centrum[afval_cols].copy()
    bomen_centrum = bomen_centrum[boom_cols].copy()

    print(f"Afvalbakken na ruimtelijke verificatie: {len(afval_centrum)}")
    print(f"Bomen na ruimtelijke verificatie: {len(bomen_centrum)}")

    OUT.mkdir(exist_ok=True)
    afval_geojson = OUT / "afvalbakken_rotterdam_centrum.geojson"
    bomen_geojson = OUT / "bomen_rotterdam_centrum.geojson"
    afval_centrum.to_file(afval_geojson, driver="GeoJSON")
    bomen_centrum.to_file(bomen_geojson, driver="GeoJSON")
    print(f"GeoJSON opgeslagen: {afval_geojson}")
    print(f"GeoJSON opgeslagen: {bomen_geojson}")

    fig, ax = plt.subplots(figsize=(12, 12))
    centrum.plot(ax=ax, color="#f6f3ee", edgecolor="#8c8377", linewidth=1.0, zorder=1)
    bomen_centrum.plot(ax=ax, color="#2d8a4e", markersize=0.8, alpha=0.45, zorder=2)
    afval_centrum.plot(ax=ax, color="#d94841", markersize=5.0, alpha=0.78, zorder=3)

    area_patch = mpatches.Patch(facecolor="#f6f3ee", edgecolor="#8c8377", label="Gebied Rotterdam Centrum")
    bomen_handle = mlines.Line2D([], [], color="#2d8a4e", marker="o", linestyle="None", markersize=4, label=f"Bomen ({len(bomen_centrum):,})")
    afval_handle = mlines.Line2D([], [], color="#d94841", marker="o", linestyle="None", markersize=7, label=f"Afvalbakken ({len(afval_centrum):,})")
    ax.legend(
        handles=[area_patch, bomen_handle, afval_handle],
        title="Legenda",
        loc="lower right",
        frameon=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="#d9d3cb",
    )

    add_scale_bar(ax, length_m=1_000)

    ax.set_title(
        "Afvalbakken en bomen in Rotterdam Centrum\nProjectstandaard met attribuutfilter + ruimtelijke verificatie",
        fontsize=15,
        fontweight="bold",
        pad=18,
    )
    ax.text(
        0.5,
        0.03,
        "Bron: Gemeente Rotterdam, SB_Infra/Afvalbak, Bomen en TIR-gebieden",
        transform=fig.transFigure,
        ha="center",
        fontsize=9,
        color="#5e5a55",
    )

    ax.set_axis_off()
    plt.tight_layout()

    out_png = OUT / "kaart_afvalbakken_bomen_rotterdam_centrum.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {out_png}")


if __name__ == "__main__":
    main()
