"""Afvalbakdichtheid per subbuurt in Rotterdam — choropleet (genormaliseerd).

Choropleet-variant van 'aantal afvalbakken per subbuurt'. Een choropleet moet
genormaliseerd zijn (invariant 3); TIR-subbuurten hebben geen inwonertal, dus
normaliseren we op oppervlak: afvalbakken per km².
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd

from rotterdam import (
    load_layer, choropleth, finalize_map, fit_figure_to_data, place_legend,
    validate_map, save_map, setup_headless_matplotlib,
)

setup_headless_matplotlib()

# 1. Data + telling + normalisatie (afvalbakken per km²)
sub = load_layer("subbuurten")
afval = load_layer("afvalbak")
j = gpd.sjoin(afval[["geometry"]], sub, how="inner", predicate="within")
sub["n_afval"] = sub.index.map(j.groupby(j.index_right).size()).fillna(0).astype(int)
sub["opp_km2"] = sub.geometry.area / 1_000_000.0
sub["afval_per_km2"] = (sub["n_afval"] / sub["opp_km2"]).round(1)
print(f"{sub['n_afval'].sum()} afvalbakken; dichtheid per km²: "
      f"mediaan {sub['afval_per_km2'].median():.1f}, max {sub['afval_per_km2'].max():.0f}")

# 2. Choropleet via de library (classificatie + styling + titel/subtitel)
fig, ax = choropleth(
    sub, "afval_per_km2", cmap="YlOrRd",
    title="Afvalbakdichtheid per subbuurt — Rotterdam",
    subtitle="afvalbakken per km² (Obsurv)",
)
finalize_map(fig, source="Obsurv (afvalbakken) + TIR-subbuurten via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

# 3. Legenda van de choropleet naar een datavrije hoek (invariant 8)
_leg = ax.get_legend()
if _leg is not None:
    _h = list(_leg.legend_handles)
    _l = [t.get_text() for t in _leg.get_texts()]
    _t = _leg.get_title().get_text()
    _leg.remove()
    place_legend(ax, _h, _l, title=_t, corner="auto", data=sub, fontsize=8)

warns = validate_map(fig, ax, data=sub, normalized=True)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out = save_map(fig, "afvalbakken_dichtheid_per_subbuurt")
print("Kaart opgeslagen:", out)
