"""Choropleet: afvalbakken per km² per buurt in Rotterdam Zuid.

Normaliseert op buurtoppervlak in plaats van inwonertal — robuust voor de
haven- en industriebuurten in Zuid (Waalhaven, Eemhaven, Vondelingenplaat)
waar bijna niemand woont maar wel afvalbakken staan. Volgt de Rotterdamse
kartografische richtlijn dat choropleten genormaliseerd moeten zijn.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")

from rotterdam import (
    CACHE,
    RD_NEW,
    ROTTERDAM_ZUID_GEBIEDEN,
    STYLE,
    choropleth,
    count_per_polygon,
    finalize_map,
    load_layer,
    save_map,
    setup_headless_matplotlib,
    validate_map,
)

setup_headless_matplotlib()

CBS_CACHE = CACHE / "cbs_buurten_rotterdam_2024.geojson"


def load_cbs_buurten_rotterdam():
    """Load CBS Wijk- en Buurtkaart 2024 Rotterdam from local cache.

    The 2024 CBS schema renamed `aantal_inwoners` → `aantalInwoners` and uses
    -99997 as a secrecy/missing code. Also, the PDOK WFS rejects CQL_FILTER but
    accepts OGC FILTER; pre-cache via curl avoids GDAL's /vsicurl HEAD-probe.
    """
    import geopandas as gpd

    if not CBS_CACHE.exists():
        raise FileNotFoundError(
            f"Cache ontbreekt: {CBS_CACHE}. Vul met:\n"
            "  curl -sS \"https://service.pdok.nl/cbs/wijkenbuurten/2024/wfs/v1_0\" ..."
        )
    gdf = gpd.read_file(CBS_CACHE).to_crs(RD_NEW)
    gdf = gdf.rename(columns={"aantalInwoners": "aantal_inwoners"})
    return gdf[gdf["aantal_inwoners"] > 0].copy()


def main() -> None:
    gebieden = load_layer("gebieden")
    afval = load_layer("afvalbak")
    cbs = load_cbs_buurten_rotterdam()

    zuid_polys = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_ZUID_GEBIEDEN)].copy()
    zuid_polys["geometry"] = zuid_polys.geometry.make_valid()
    zuid_union = zuid_polys.geometry.unary_union

    cbs_zuid = cbs[cbs.geometry.representative_point().within(zuid_union)].copy()
    cbs_zuid["opp_km2"] = cbs_zuid.geometry.area / 1_000_000
    afval_zuid = afval[afval.geometry.within(zuid_union)].copy()

    print(f"Buurten in Zuid (CBS): {len(cbs_zuid)}")
    print(f"Afvalbakken in Zuid: {len(afval_zuid):,}")

    per_buurt = count_per_polygon(
        afval_zuid,
        cbs_zuid,
        key="buurtnaam",
        normalize_by="opp_km2",
        per=1,
    )

    rate_stats = per_buurt["rate"].dropna()
    print(
        f"Dichtheid afvalbakken/km² — median: {rate_stats.median():.1f}, "
        f"p90: {rate_stats.quantile(0.9):.1f}, max: {rate_stats.max():.1f}"
    )
    top5 = per_buurt.nlargest(5, "rate")[["buurtnaam", "n", "opp_km2", "rate"]]
    print("\nTop 5 dichtste buurten (afvalbakken per km²):")
    for _, r in top5.iterrows():
        print(
            f"  - {r.buurtnaam}: {int(r.n)} bakken / {r.opp_km2:.2f} km² "
            f"= {r.rate:.0f} per km²"
        )

    fig, ax = choropleth(
        per_buurt,
        "rate",
        title="Afvalbakken in Rotterdam Zuid",
        subtitle="Dichtheid per buurt — afvalbakken per km² (CBS-buurten 2024)",
        cmap="YlOrRd",
        scheme="quantiles",
        k=5,
        legend_label="per km²",
    )

    zuid_polys.boundary.plot(
        ax=ax,
        color="#1a1a1a",
        linewidth=0.9,
        zorder=4,
    )

    import matplotlib.patheffects as pe

    for _, row in zuid_polys.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        centroid = row.geometry.representative_point()
        txt = ax.text(
            centroid.x,
            centroid.y,
            row["GEBDNAAM"],
            ha="center",
            va="center",
            fontsize=9,
            color=STYLE["title_color"],
            weight="bold",
            zorder=5,
        )
        txt.set_path_effects([pe.withStroke(linewidth=2.5, foreground="white")])

    finalize_map(
        fig,
        source="Obsurv (afvalbak) + CBS Wijk- en Buurtkaart 2024 + TIR-gebieden",
    )

    warns = validate_map(fig, ax, data=per_buurt, normalized=True, n_classes=5)
    if warns:
        print("\nValidatie-waarschuwingen:")
        for w in warns:
            print(f"  - {w}")

    out = save_map(fig, "kaart_afvalbakken_zuid_dichtheid_per_km2")
    print(f"\nKaart opgeslagen: {out}")


if __name__ == "__main__":
    main()
