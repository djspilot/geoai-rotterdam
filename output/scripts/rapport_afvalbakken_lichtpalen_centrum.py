"""PDF-rapport: kaart + tabel afvalbakken/lichtpalen per straat in Rotterdam Centrum."""

from __future__ import annotations

import sys

sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")

import geopandas as gpd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import pandas as pd

from rotterdam import (
    ARCGIS_LAYERS,
    ASSET_COLORS,
    REPORTS_DIR,
    STYLE,
    fetch_arcgis_layer,
    finalize_map,
    load_layer,
    setup_headless_matplotlib,
    style_map,
)

setup_headless_matplotlib()
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

CENTRUM = "Rotterdam Centrum"
ROWS_PER_PAGE = 60


def spatial_filter(points: gpd.GeoDataFrame, polygon: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return gpd.sjoin(points, polygon[["geometry"]], how="inner", predicate="within").drop(
        columns="index_right"
    )


def map_page(pdf: PdfPages, centrum, afval, licht) -> None:
    fig, ax = plt.subplots(figsize=(11.7, 8.3))  # A4 landscape
    centrum.plot(ax=ax, facecolor=STYLE["polygon_fill"],
                 edgecolor=STYLE["boundary_color"], linewidth=1.0, zorder=1)
    licht.plot(ax=ax, color=ASSET_COLORS["lichtpunten"],
               markersize=3.5, alpha=0.6, zorder=2)
    afval.plot(ax=ax, color=ASSET_COLORS["afvalbak"],
               markersize=5.5, alpha=0.85, zorder=3)

    style_map(ax, title=f"Afvalbakken en lichtpalen in {CENTRUM}")
    area = mpatches.Patch(facecolor=STYLE["polygon_fill"],
                          edgecolor=STYLE["boundary_color"],
                          label=f"Gebied {CENTRUM}")
    afval_h = mlines.Line2D([], [], color=ASSET_COLORS["afvalbak"], marker="o",
                            linestyle="None", markersize=7,
                            label=f"Afvalbakken (n={len(afval):,})")
    licht_h = mlines.Line2D([], [], color=ASSET_COLORS["lichtpunten"], marker="o",
                            linestyle="None", markersize=6,
                            label=f"Lichtpalen (n={len(licht):,})")
    ax.legend(handles=[area, afval_h, licht_h], title="Legenda",
              loc="lower right", frameon=True, facecolor="white",
              edgecolor=STYLE["separator_color"], fontsize=9)

    finalize_map(fig,
                 source="Obsurv via diensten.rotterdam.nl (Afvalbak, LICHTPUNTEN) + TIR-gebieden")
    pdf.savefig(fig, bbox_inches="tight", facecolor=STYLE["fig_bg"])
    plt.close(fig)


def table_pages(pdf: PdfPages, tabel: pd.DataFrame) -> None:
    total_pages = (len(tabel) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
    for i in range(total_pages):
        chunk = tabel.iloc[i * ROWS_PER_PAGE : (i + 1) * ROWS_PER_PAGE].reset_index()
        fig, ax = plt.subplots(figsize=(8.3, 11.7))  # A4 portrait
        ax.set_axis_off()

        title = f"Afvalbakken en lichtpalen per straat — {CENTRUM}"
        subtitle = (
            f"Pagina {i + 1}/{total_pages}  ·  "
            f"Straten: {len(tabel)}  ·  "
            f"Totaal afvalbakken: {tabel['afvalbakken'].sum():,}  ·  "
            f"Totaal lichtpalen: {tabel['lichtpalen'].sum():,}"
        )
        fig.text(0.05, 0.96, title, fontsize=14, fontweight="bold",
                 color=STYLE["title_color"])
        fig.text(0.05, 0.935, subtitle, fontsize=9, color=STYLE["subtitle_color"])

        cell_text = [
            [str(row["straat"]), f"{int(row['afvalbakken']):,}",
             f"{int(row['lichtpalen']):,}"]
            for _, row in chunk.iterrows()
        ]
        table = ax.table(
            cellText=cell_text,
            colLabels=["Straat", "Afvalbakken", "Lichtpalen"],
            colWidths=[0.55, 0.20, 0.20],
            cellLoc="left",
            colLoc="left",
            loc="upper center",
            bbox=[0.0, 0.02, 1.0, 0.90],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8.5)
        for (r, c), cell in table.get_celld().items():
            cell.set_edgecolor(STYLE["separator_color"])
            cell.set_linewidth(0.4)
            if r == 0:
                cell.set_facecolor("#efe9df")
                cell.set_text_props(weight="bold", color=STYLE["title_color"])
            if c in (1, 2):
                cell.set_text_props(ha="right")
                cell._loc = "right"

        fig.text(0.05, 0.02,
                 "Bron: Obsurv via diensten.rotterdam.nl (Afvalbak, LICHTPUNTEN) + TIR-gebieden",
                 fontsize=7.5, color=STYLE["footer_color"])
        pdf.savefig(fig, facecolor=STYLE["fig_bg"])
        plt.close(fig)


def main() -> None:
    gebieden = load_layer("gebieden")
    centrum = gebieden[gebieden["GEBDNAAM"] == CENTRUM].copy()
    centrum["geometry"] = centrum.geometry.make_valid()

    afval = load_layer("afvalbak")
    afval_c = spatial_filter(afval[afval["WOONPLAATS"] == CENTRUM], centrum)

    licht_fc = fetch_arcgis_layer(
        ARCGIS_LAYERS["lichtpunten"], where="WOONPLAATS='Rotterdam Centrum'"
    )
    licht = gpd.GeoDataFrame.from_features(licht_fc["features"], crs="EPSG:28992")
    licht_c = spatial_filter(licht, centrum)

    tabel = (
        pd.concat(
            [
                afval_c.groupby("STRAAT").size().rename("afvalbakken"),
                licht_c.groupby("STRAAT").size().rename("lichtpalen"),
            ],
            axis=1,
        )
        .fillna(0)
        .astype(int)
        .sort_values(["afvalbakken", "lichtpalen"], ascending=False)
    )
    tabel.index.name = "straat"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "rapport_afvalbakken_lichtpalen_centrum.pdf"
    with PdfPages(out) as pdf:
        map_page(pdf, centrum, afval_c, licht_c)
        table_pages(pdf, tabel)

    print(f"Afvalbakken: {len(afval_c):,}  ·  Lichtpalen: {len(licht_c):,}  ·  "
          f"Straten: {len(tabel)}")
    print(f"PDF opgeslagen: {out}")


if __name__ == "__main__":
    main()
