"""Locaties van alle laadpalen in Rotterdam.

Gemaakt met de rotterdam-geoai skill. Onderwerp: alle laadpalen (Obsurv/SB_Infra
Laadpalen) in de gemeente Rotterdam, uniform weergegeven (geen indeling naar
type/beheerder — dat is niet gevraagd).

Kaarttype: puntenkaart (locaties tonen). Titel volgens invariant 19, legenda
datavrij geplaatst (invariant 8) met NL-getalnotatie (invariant 16).
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, fetch_arcgis_layer, style_map, finalize_map, fit_figure_to_data,
    place_legend, add_rotterdam_basemap, add_pdok_basemap, validate_map, save_map,
    setup_headless_matplotlib, nl_getal, RD_NEW, CACHE, ARCGIS_LAYERS,
)

setup_headless_matplotlib()

LAAD_URL = ARCGIS_LAYERS["laadpalen"]
CACHE_FILE = CACHE / "laadpalen.geojson"
LAAD_KLEUR = "#2ca25f"                    # groen (elektrisch vervoer)

# 1. Laadpalen ophalen (met cache)
if CACHE_FILE.exists():
    laad = gpd.read_file(CACHE_FILE)
else:
    CACHE.mkdir(parents=True, exist_ok=True)
    fc = fetch_arcgis_layer(LAAD_URL)
    laad = gpd.GeoDataFrame.from_features(fc["features"], crs=RD_NEW)
    laad.to_file(CACHE_FILE, driver="GeoJSON")
print(f"{len(laad)} laadpalen in Rotterdam")

gemeente = load_layer("gemeente")

# 2. Tekenen: gemeentegrens als context + de laadpaal-locaties
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
gemeente.boundary.plot(ax=ax, color="#333333", linewidth=1.0, zorder=4)
laad.plot(ax=ax, color=LAAD_KLEUR, markersize=7, edgecolor="white",
          linewidth=0.2, alpha=0.85, zorder=6)

# 3. Gekleurde Rotterdam-basemap (inv. 10), met PDOK-fallback (inv. 12)
bron = "Obsurv (Laadpalen) via diensten.rotterdam.nl"
try:
    add_rotterdam_basemap(ax, layer="kleur")
except Exception as e:
    print("Rotterdam-basemap faalde, val terug op PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron += " · Basiskaart: PDOK BRT"

# 4. Titel (inv. 19: wat+waar in hoofdtitel, nuance/periode in subtitel) + footer
style_map(ax, "Laadpalen — Rotterdam",
          subtitle="laadpalen elektrisch vervoer · situatie 2026")
finalize_map(fig, source=bron)
fit_figure_to_data(fig, ax)

# 5. Datavrije legenda (inv. 8), NL-getalnotatie (inv. 16)
handle = Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=LAAD_KLEUR,
                markeredgecolor="white", markersize=9,
                label=f"Laadpaal ({nl_getal(len(laad))})")
place_legend(ax, [handle], [handle.get_label()], title="Legenda",
             corner="auto", data=laad)

warns = validate_map(fig, ax, data=laad)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out = save_map(fig, "laadpalen_rotterdam")
print("Kaart opgeslagen:", out)
