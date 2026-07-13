"""Kaart van Rotterdam Zuid: afvalbakken als puntenkaart binnen de Zuid-gebieden.

Rotterdam Zuid = ROTTERDAM_ZUID_GEBIEDEN: Charlois, Feijenoord, Hoogvliet,
IJsselmonde, Pernis, Rozenburg, Vondelingenplaat, Waalhaven-Eemhaven
(zie rotterdam.vocab). Bron: Obsurv via diensten.rotterdam.nl.
"""

import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

from rotterdam import (
    load_layer, filter_to_area, point_map, finalize_map, validate_map, save_map,
    setup_headless_matplotlib, ROTTERDAM_ZUID_GEBIEDEN,
)

setup_headless_matplotlib()

gebieden = load_layer("gebieden")
afval = load_layer("afvalbak")

zuid_grens = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_ZUID_GEBIEDEN)]
zuid = filter_to_area(afval, gebieden, gebied_names=ROTTERDAM_ZUID_GEBIEDEN)

fig, ax = point_map(
    zuid,
    boundary=zuid_grens,
    title="Afvalbakken in Rotterdam Zuid",
)
finalize_map(
    fig,
    source="Obsurv via diensten.rotterdam.nl",
    suptitle=None,
)
validate_map(fig, ax, data=zuid)
out = save_map(fig, "kaart_rotterdam_zuid")
print(f"Afvalbakken in Zuid: {len(zuid)}")
print(f"Gebieden: {', '.join(sorted(ROTTERDAM_ZUID_GEBIEDEN))}")
print(f"SAVED: {out}")
