"""Alle speelplaatsen in Rotterdam Centrum (één uniforme weergave).

Gemaakt met de rotterdam-geoai skill: speelplekken (Obsurv/SB_Infra) gefilterd op
gebied Rotterdam Centrum, op de gekleurde Rotterdam-basemap, met de conventies
(titel/subtitel boven de kaart, datavrije legenda, footer met bron).
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, fetch_arcgis_layer, style_map, finalize_map, fit_figure_to_data,
    place_legend, add_rotterdam_basemap, add_pdok_basemap, validate_map, save_map,
    setup_headless_matplotlib, RD_NEW, CACHE,
)

setup_headless_matplotlib()

SPEEL_URL = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Speelplekken/MapServer/0"
CACHE_FILE = CACHE / "speelplekken.geojson"
SPEEL_KLEUR = "#2c7fb8"

# 1. Speelplekken (met cache)
if CACHE_FILE.exists():
    speel = gpd.read_file(CACHE_FILE)
else:
    CACHE.mkdir(parents=True, exist_ok=True)
    fc = fetch_arcgis_layer(SPEEL_URL)
    speel = gpd.GeoDataFrame.from_features(fc["features"], crs=RD_NEW)
    speel.to_file(CACHE_FILE, driver="GeoJSON")

gebieden = load_layer("gebieden")
buurten = load_layer("buurten")
centrum = gebieden[gebieden["GEBDNAAM"] == "Rotterdam Centrum"]
centrum_buurten = buurten[buurten["GEBDNAAM"] == "Rotterdam Centrum"]
speel_c = speel[speel.intersects(centrum.geometry.iloc[0])].copy()
print(f"{len(speel_c)} speelplaatsen in Rotterdam Centrum")

# 2. Tekenen: buurtgrenzen (witte casing) + alle speelplaatsen (uniform)
fig, ax = plt.subplots(figsize=(11, 11))
ax.set_aspect("equal")
casing = [pe.withStroke(linewidth=2.0, foreground="white")]
centrum_buurten.boundary.plot(ax=ax, color="#555555", linewidth=0.5, zorder=5,
                              path_effects=casing)
centrum.boundary.plot(ax=ax, color="#111111", linewidth=1.6, zorder=6,
                      path_effects=casing)
speel_c.plot(ax=ax, facecolor=SPEEL_KLEUR, edgecolor="white", linewidth=0.4,
             alpha=0.95, zorder=7)

# 3. Gekleurde Rotterdam-basemap (inv. 10), met PDOK-fallback (inv. 12)
bron = "Obsurv (Speelplekken) + TIR via diensten.rotterdam.nl"
try:
    add_rotterdam_basemap(ax, layer="kleur")
except Exception as e:
    print("Rotterdam-basemap faalde, val terug op PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron += " · Basiskaart: PDOK BRT"

# 4. Kaartelementen + footer + datavrije legenda
style_map(ax, "Speelplaatsen in Rotterdam Centrum",
          subtitle=f"{len(speel_c)} speelplekken")
# tight_bottom: kleinere ondermarge (geen schaalstok in de kaart);
# fit_figure_to_data: figuurhoogte op de Centrum-vorm passen (geen witruimte)
finalize_map(fig, source=bron, tight_bottom=True)
fit_figure_to_data(fig, ax)
handles = [
    Patch(facecolor=SPEEL_KLEUR, edgecolor="white", label=f"Speelplaats ({len(speel_c)})"),
    Line2D([0], [0], color="#111111", linewidth=1.6, label="Gebiedsgrens"),
]
place_legend(ax, handles, [h.get_label() for h in handles],
             title="Legenda", corner="auto", data=speel_c)

warns = validate_map(fig, ax, data=speel_c)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out = save_map(fig, "speelplaatsen_rotterdam_centrum")
print("Kaart opgeslagen:", out)
