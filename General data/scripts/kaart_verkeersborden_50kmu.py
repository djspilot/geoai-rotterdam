"""Locaties van verkeersborden 'maximumsnelheid 50 km/u' in Rotterdam (situatie 2026).

Gemaakt met de rotterdam-geoai skill. Onderwerp: locaties van de A1-borden
(RVV maximumsnelheid) met 50 km/u. Bron: Obsurv/SB_Infra Verkeersborden.

Interpretatie "in 2026": het veld PLAATSINGSJAAR kent geen borden uit 2026
(nieuwste = 2024), dus "in 2026" = de actuele registratie/situatie in 2026,
niet "geplaatst in 2026".

Kaarttype: puntenkaart (locaties tonen). Eén uniforme categorie (invariant 3:
geen ruwe-count-choropleet). Titel volgens invariant 19, legenda datavrij
geplaatst (invariant 8) met NL-getalnotatie (invariant 16).
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, fetch_arcgis_layer, style_map, finalize_map, fit_figure_to_data,
    place_legend, add_rotterdam_basemap, add_pdok_basemap, validate_map, save_map,
    setup_headless_matplotlib, nl_getal, RD_NEW, CACHE,
)

setup_headless_matplotlib()

BORD_URL = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Verkeersborden/MapServer/0"
WHERE = "MODELNUMMER LIKE 'A0150%'"      # A1 maximumsnelheid 50 km/u (alle varianten)
CACHE_FILE = CACHE / "verkeersborden_50kmu.geojson"
BORD_KLEUR = "#d42027"                    # RVV-rood

# 1. Borden ophalen (met cache)
if CACHE_FILE.exists():
    borden = gpd.read_file(CACHE_FILE)
else:
    CACHE.mkdir(parents=True, exist_ok=True)
    fc = fetch_arcgis_layer(BORD_URL, where=WHERE)
    borden = gpd.GeoDataFrame.from_features(fc["features"], crs=RD_NEW)
    borden.to_file(CACHE_FILE, driver="GeoJSON")
print(f"{len(borden)} borden 'maximumsnelheid 50 km/u' in Rotterdam")

gemeente = load_layer("gemeente")

# 2. Tekenen: gemeentegrens als context + de bordlocaties
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
gemeente.boundary.plot(ax=ax, color="#333333", linewidth=1.0, zorder=4)
borden.plot(ax=ax, color=BORD_KLEUR, markersize=26, edgecolor="white",
            linewidth=0.5, alpha=0.95, zorder=6)

# 3. Gekleurde Rotterdam-basemap (inv. 10), met PDOK-fallback (inv. 12)
bron = "Obsurv (Verkeersborden) via diensten.rotterdam.nl"
try:
    add_rotterdam_basemap(ax, layer="kleur")
except Exception as e:
    print("Rotterdam-basemap faalde, val terug op PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron += " · Basiskaart: PDOK BRT"

# 4. Titel (inv. 19: wat+waar in hoofdtitel, eenheid/periode in subtitel) + footer
style_map(ax, "Verkeersborden maximumsnelheid 50 km/u — Rotterdam",
          subtitle="RVV-model A1 · situatie 2026")
finalize_map(fig, source=bron)
fit_figure_to_data(fig, ax)

# 5. Datavrije legenda (inv. 8), NL-getalnotatie (inv. 16)
handle = Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=BORD_KLEUR,
                markeredgecolor="white", markersize=9,
                label=f"Maximumsnelheid 50 km/u ({nl_getal(len(borden))})")
place_legend(ax, [handle], [handle.get_label()], title="Legenda",
             corner="auto", data=borden)

warns = validate_map(fig, ax, data=borden)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out = save_map(fig, "verkeersborden_50kmu")
print("Kaart opgeslagen:", out)
