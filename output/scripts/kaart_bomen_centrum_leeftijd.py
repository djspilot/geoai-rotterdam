"""Bomen in Rotterdam Centrum, geclassificeerd naar leeftijd (per 10 jaar).

Alle bomen binnen het gebied Rotterdam Centrum, gekleurd naar leeftijd in stappen
van 10 jaar (0–9, 10–19, … 90–99) met een top-klasse ≥ 100 jaar (de decennia
boven de 100 zijn dun bezet). Kleurverloop geel (jong) → donkerpaars (oud).

Leeftijd = huidig jaar − `AANLEGJAAR` (plantjaar). Bomen zonder geldig plantjaar
worden weggelaten. De bomen worden op het gebied Rotterdam Centrum geknipt; de
selectie wordt in de project-cache bewaard zodat herhaald draaien niet de hele
bomenlaag (~200k) opnieuw hoeft te klippen.

Grijze basemap (afwijking van de kleur-default, invariant 10): bij deze dichte,
geclassificeerde puntenkaart geeft grijs het beste contrast voor de kleuren.

Bron: Obsurv / Gemeente Rotterdam (bomenbeheer, veld AANLEGJAAR).
"""

import os
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, style_map, add_scalebar, add_rotterdam_basemap, add_pdok_basemap,
    finalize_map, fit_figure_to_data, place_legend, save_map,
    setup_headless_matplotlib, CACHE, RD_NEW,
)

setup_headless_matplotlib()
NU = date.today().year

# --- bomen in Rotterdam Centrum (uit project-cache of vers geknipt) ----------
geb = load_layer("gebieden").to_crs(RD_NEW)
centrum = geb[geb["GEBDNAAM"] == "Rotterdam Centrum"]

cache_file = os.path.join(str(CACHE), "bomen_centrum.geojson")
if os.path.exists(cache_file):
    bomen = gpd.read_file(cache_file)
else:
    bomen = gpd.clip(load_layer("bomen").to_crs(RD_NEW), centrum)
    os.makedirs(str(CACHE), exist_ok=True)
    bomen.to_file(cache_file, driver="GeoJSON")

# --- leeftijd -> klasse per 10 jaar (top = 100+); rest -> 'Onbekend' ----------
geldig = (bomen["AANLEGJAAR"] > 1800) & (bomen["AANLEGJAAR"] <= NU)
b = bomen[geldig].copy()
b["leeftijd"] = NU - b["AANLEGJAAR"]
K = 11                                        # 0-9 … 90-99, 100+
b["klasse"] = np.minimum(b["leeftijd"] // 10, K - 1).astype(int)
onbekend = bomen[~geldig]                     # leeg of placeholder 1800
print(f"bomen met leeftijd: {len(b)} | onbekend plantjaar: {len(onbekend)}")

labels = [f"{i*10}–{i*10+9} jaar" for i in range(K - 1)] + ["≥ 100 jaar"]
cmap = plt.get_cmap("viridis_r")              # jong = licht (geel), oud = donker
colors = [cmap(i / (K - 1)) for i in range(K)]
ONBEKEND = "#969696"                          # grijs voor onbekend plantjaar

xy = np.column_stack([b.geometry.x.to_numpy(), b.geometry.y.to_numpy()])
kl = b["klasse"].to_numpy()

# --- kaart -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 12))
centrum.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=4)
for i in range(K):
    m = kl == i
    if m.any():
        ax.scatter(xy[m, 0], xy[m, 1], s=5, color=colors[i], edgecolor="none",
                   zorder=5 + i)
# 'Onbekend' bovenop, iets groter met witte rand zodat de 8 bomen opvallen
if len(onbekend):
    ax.scatter(onbekend.geometry.x, onbekend.geometry.y, s=16, color=ONBEKEND,
               edgecolor="white", linewidths=0.5, zorder=5 + K)

bron_delen = ["Bomen: Obsurv/Gemeente Rotterdam"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as e:
    print("fallback PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "Bomen in Rotterdam Centrum naar leeftijd (per 10 jaar)")
add_scalebar(ax, inside=True)
finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# legenda ná fit_figure_to_data (invariant 8: juiste maat -> juiste plaatsing)
handles = [Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=colors[i],
                  markeredgecolor="none", markersize=7, label=labels[i])
           for i in range(K)]
if len(onbekend):
    handles.append(Line2D([0], [0], marker="o", linestyle="none",
                          markerfacecolor=ONBEKEND, markeredgecolor="white",
                          markersize=7, label=f"Onbekend (n={len(onbekend)})"))
place_legend(ax, handles=handles, corner="auto", title="Legenda")

print("opgeslagen:", save_map(fig, "bomen_centrum_leeftijd"))
