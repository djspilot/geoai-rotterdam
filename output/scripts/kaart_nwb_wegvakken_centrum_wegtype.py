"""NWB-wegvakken in Rotterdam Centrum, gecategoriseerd naar wegtype (baansoort).

Alle wegvakken uit het Nationaal Wegenbestand (NWB, Rijkswaterstaat via PDOK)
binnen het gebied Rotterdam Centrum, gekleurd naar wegtype. Het NWB-veld
`wegtype`/`wgtypeOms` is leeg voor gemeentelijke wegen, dus we categoriseren op
`bstCode` (baansoort): Rijbaan, Fietspad, Voetpad, Busbaan, en de rest → Overig.

De wegvakken worden via `nwb_wegvakken(bbox)` opgehaald (PDOK-WFS, gepagineerd,
EPSG:28992) voor de Centrum-bbox en op het gebied geknipt. De selectie wordt in
de project-cache bewaard.

Grijze basemap (afwijking van de kleur-default, invariant 10): bij dit dichte
lijnennet geeft grijs het beste contrast voor de categorie-kleuren.

Bron: NWB — Nationaal Wegenbestand (Rijkswaterstaat), via PDOK. Zie national_sources.md.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, nwb_wegvakken, style_map, add_scalebar, add_rotterdam_basemap,
    add_pdok_basemap, finalize_map, fit_figure_to_data, place_legend, save_map,
    setup_headless_matplotlib, CACHE, RD_NEW,
)

setup_headless_matplotlib()

# --- NWB-wegvakken in Rotterdam Centrum --------------------------------------
geb = load_layer("gebieden").to_crs(RD_NEW)
centrum = geb[geb["GEBDNAAM"] == "Rotterdam Centrum"]

cache_file = os.path.join(str(CACHE), "nwb_wegvakken_centrum.geojson")
if os.path.exists(cache_file):
    wv = gpd.read_file(cache_file)
else:
    wv = gpd.clip(nwb_wegvakken(tuple(centrum.total_bounds)), centrum)
    wv = wv[~wv.geometry.is_empty & wv.geometry.notna()]
    os.makedirs(str(CACHE), exist_ok=True)
    wv.to_file(cache_file, driver="GeoJSON")

# --- baansoort (bstCode) -> wegtype-categorie --------------------------------
NAAM = {"RB": "Rijbaan", "FP": "Fietspad", "VP": "Voetpad", "BUS": "Busbaan"}
wv["wegtype"] = wv["bstCode"].map(NAAM).fillna("Overig")
print(wv["wegtype"].value_counts().to_string())

ORDER = ["Rijbaan", "Fietspad", "Voetpad", "Busbaan", "Overig"]
COLORS = {"Rijbaan": "#4d4d4d", "Fietspad": "#e31a1c", "Voetpad": "#fdae61",
          "Busbaan": "#3182bd", "Overig": "#bdbdbd"}
LW = {"Rijbaan": 1.6, "Fietspad": 1.0, "Voetpad": 0.8, "Busbaan": 1.2, "Overig": 0.8}

# --- kaart -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 12))
centrum.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=3)
for cat in ["Overig"] + ORDER[:-1]:          # Overig onderop, rest erbovenop
    sub = wv[wv["wegtype"] == cat]
    if len(sub):
        sub.plot(ax=ax, color=COLORS[cat], linewidth=LW[cat],
                 zorder=5 + ORDER.index(cat))

bron_delen = ["Wegvakken: NWB (PDOK/Rijkswaterstaat)"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as e:
    print("fallback PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "NWB-wegvakken in Rotterdam Centrum naar wegtype (baansoort)")
add_scalebar(ax, inside=True)
finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# legenda ná fit_figure_to_data (invariant 8)
present = [c for c in ORDER if (wv["wegtype"] == c).any()]
handles = [Line2D([0], [0], color=COLORS[c], lw=max(LW[c], 2.5),
                  label=f"{c} (n={int((wv['wegtype'] == c).sum())})") for c in present]
place_legend(ax, handles=handles, corner="auto", title="Legenda")

print("opgeslagen:", save_map(fig, "nwb_wegvakken_centrum_wegtype"))
