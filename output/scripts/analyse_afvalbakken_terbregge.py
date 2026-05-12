"""Analyse afvalbakken en knelpuntzones voor Terbregge (Nieuw-Terbregge in praktijk)."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "General data" / "Data"
OUT = PROJECT / "output"

WIJK_NAAM = "Terbregge"
SERVICE_RADIUS_M = 150
MIN_KNELPUNT_M2 = 7_500


def load_rotterdam(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    minx, miny, _, _ = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)


def add_scale_bar(ax, length_m=500):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    x0 = minx + (maxx - minx) * 0.05
    y0 = miny + (maxy - miny) * 0.04
    x1 = x0 + length_m
    ax.plot([x0, x1], [y0, y0], color="#222", linewidth=2.0)
    ax.plot([x0, x0], [y0 - 40, y0 + 40], color="#222", linewidth=1.4)
    ax.plot([x1, x1], [y0 - 40, y0 + 40], color="#222", linewidth=1.4)
    ax.text((x0 + x1) / 2, y0 + 90, "500 m", ha="center", va="bottom", fontsize=9)


def main() -> None:
    OUT.mkdir(exist_ok=True)

    buurten = load_rotterdam(DATA / "tir_buurten.geojson")
    afval = load_rotterdam(DATA / "afvalbak.geojson")

    wijk = buurten[buurten["BUURTNAAM"] == WIJK_NAAM].copy()
    if wijk.empty:
        raise ValueError(f"Wijk '{WIJK_NAAM}' niet gevonden in tir_buurten.geojson")
    wijk["geometry"] = wijk.geometry.make_valid()

    afval_attr = afval[afval["WIJK"] == WIJK_NAAM].copy()
    afval_wijk = gpd.sjoin(afval_attr, wijk[["BUURTNAAM", "geometry"]], how="inner", predicate="within")
    keep_cols = [c for c in ["WOONPLAATS", "WIJK", "STRAAT", "TYPE", "geometry"] if c in afval_wijk.columns]
    afval_wijk = afval_wijk[keep_cols].copy()

    count_total = len(afval_wijk)
    print(f"Afvalbakken in {WIJK_NAAM}: {count_total}")

    straat_telling = (
        afval_wijk["STRAAT"].fillna("Onbekend")
        .astype(str)
        .value_counts()
        .head(10)
    )
    print("Topstraten met meeste afvalbakken:")
    print(straat_telling.to_string())

    # Knelpunten: delen van de wijk die buiten 150m servicegebied van een afvalbak vallen.
    wijk_union = wijk.unary_union
    if count_total > 0:
        service_union = afval_wijk.geometry.buffer(SERVICE_RADIUS_M).unary_union
        uncovered = wijk_union.difference(service_union)
    else:
        uncovered = wijk_union

    if uncovered.is_empty:
        knelpunten_gdf = gpd.GeoDataFrame({"opp_m2": []}, geometry=[], crs="EPSG:28992")
    else:
        parts = list(uncovered.geoms) if uncovered.geom_type == "MultiPolygon" else [uncovered]
        knelpunten_gdf = gpd.GeoDataFrame(geometry=parts, crs="EPSG:28992")
        knelpunten_gdf["opp_m2"] = knelpunten_gdf.area
        knelpunten_gdf = knelpunten_gdf[knelpunten_gdf["opp_m2"] >= MIN_KNELPUNT_M2].copy()

    total_uncovered = float(knelpunten_gdf["opp_m2"].sum()) if not knelpunten_gdf.empty else 0.0
    wijk_area = float(wijk_union.area)
    uncovered_pct = (total_uncovered / wijk_area * 100) if wijk_area > 0 else 0.0

    print(f"Knelpuntzones (>={MIN_KNELPUNT_M2:,} m2): {len(knelpunten_gdf)}")
    print(f"Totale knelpuntoppervlakte: {total_uncovered:,.0f} m2 ({uncovered_pct:.1f}% van de wijk)")

    if not knelpunten_gdf.empty:
        top_knel = knelpunten_gdf.sort_values("opp_m2", ascending=False).head(5).copy()
        top_knel["rank"] = range(1, len(top_knel) + 1)
        print("Top 5 grootste knelpunten (m2):")
        print(top_knel[["rank", "opp_m2"]].to_string(index=False))

    # Exporteer data
    afval_out = OUT / "afvalbakken_terbregge.geojson"
    knel_out = OUT / "knelpunten_afvalbakken_terbregge.geojson"
    afval_wijk.to_file(afval_out, driver="GeoJSON")
    knelpunten_gdf.to_file(knel_out, driver="GeoJSON")
    print(f"GeoJSON opgeslagen: {afval_out}")
    print(f"GeoJSON opgeslagen: {knel_out}")

    # Kaart
    fig, ax = plt.subplots(figsize=(12, 10))
    wijk.plot(ax=ax, color="#f5f2ec", edgecolor="#8b8275", linewidth=1.0, zorder=1)

    if not knelpunten_gdf.empty:
        knelpunten_gdf.plot(ax=ax, color="#ffd166", edgecolor="#e09f00", linewidth=0.8, alpha=0.75, zorder=2)

    if count_total > 0:
        afval_wijk.plot(ax=ax, color="#d94841", markersize=18, alpha=0.85, zorder=3)

    # Labels voor grootste knelpunten
    if not knelpunten_gdf.empty:
        top = knelpunten_gdf.sort_values("opp_m2", ascending=False).head(3).copy()
        for i, (_, row) in enumerate(top.iterrows(), start=1):
            pt = row.geometry.representative_point()
            txt = ax.text(pt.x, pt.y, f"K{i}", fontsize=10, weight="bold", color="#4a3900", ha="center", va="center", zorder=4)
            txt.set_path_effects([pe.withStroke(linewidth=2.2, foreground="white")])

    add_scale_bar(ax)

    handles = [
        mpatches.Patch(facecolor="#f5f2ec", edgecolor="#8b8275", label="Wijk Terbregge"),
        mlines.Line2D([], [], color="#d94841", marker="o", linestyle="None", markersize=8, label=f"Afvalbakken ({count_total})"),
        mpatches.Patch(facecolor="#ffd166", edgecolor="#e09f00", label=f"Knelpuntzones buiten {SERVICE_RADIUS_M}m"),
    ]
    ax.legend(handles=handles, title="Legenda", loc="lower right", frameon=True, framealpha=0.95)

    ax.set_title(
        f"Afvalbakken en knelpunten in {WIJK_NAAM}\nKnelpunt = buiten {SERVICE_RADIUS_M} meter van dichtstbijzijnde afvalbak",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    ax.text(
        0.5,
        0.03,
        f"Totaal afvalbakken: {count_total} | Knelpuntoppervlak: {total_uncovered:,.0f} m2 ({uncovered_pct:.1f}%)",
        transform=fig.transFigure,
        ha="center",
        fontsize=10,
        color="#555",
    )
    ax.set_axis_off()
    plt.tight_layout()

    png_out = OUT / "kaart_afvalbakken_knelpunten_terbregge.png"
    fig.savefig(png_out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Kaart opgeslagen: {png_out}")


if __name__ == "__main__":
    main()
