"""Aantal afvalbakken en lichtpalen per straat in Rotterdam Centrum."""

from __future__ import annotations

import sys

sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")

import geopandas as gpd
import pandas as pd

from rotterdam import (
    ARCGIS_LAYERS,
    DATA_OUT,
    fetch_arcgis_layer,
    load_layer,
)

CENTRUM = "Rotterdam Centrum"


def main() -> None:
    gebieden = load_layer("gebieden")
    centrum = gebieden[gebieden["GEBDNAAM"] == CENTRUM].copy()
    centrum["geometry"] = centrum.geometry.make_valid()

    afval = load_layer("afvalbak")
    afval_c = afval[afval["WOONPLAATS"] == CENTRUM]
    afval_c = gpd.sjoin(afval_c, centrum[["geometry"]], predicate="within").drop(
        columns="index_right"
    )

    licht_fc = fetch_arcgis_layer(
        ARCGIS_LAYERS["lichtpunten"], where="WOONPLAATS='Rotterdam Centrum'"
    )
    licht = gpd.GeoDataFrame.from_features(licht_fc["features"], crs="EPSG:28992")
    licht_c = gpd.sjoin(licht, centrum[["geometry"]], predicate="within").drop(
        columns="index_right"
    )

    afval_per_straat = (
        afval_c.groupby("STRAAT").size().rename("afvalbakken")
    )
    licht_per_straat = (
        licht_c.groupby("STRAAT").size().rename("lichtpalen")
    )
    tabel = (
        pd.concat([afval_per_straat, licht_per_straat], axis=1)
        .fillna(0)
        .astype(int)
        .sort_values(["afvalbakken", "lichtpalen"], ascending=False)
    )
    tabel.index.name = "straat"

    print(f"Straten met assets in {CENTRUM}: {len(tabel)}")
    print(f"Totaal afvalbakken: {tabel['afvalbakken'].sum():,}")
    print(f"Totaal lichtpalen: {tabel['lichtpalen'].sum():,}\n")

    with pd.option_context("display.max_rows", None, "display.width", 100):
        print(tabel.to_string())

    DATA_OUT.mkdir(parents=True, exist_ok=True)
    out_csv = DATA_OUT / "afvalbakken_lichtpalen_per_straat_centrum.csv"
    tabel.to_csv(out_csv)
    print(f"\nCSV opgeslagen: {out_csv}")


if __name__ == "__main__":
    main()
