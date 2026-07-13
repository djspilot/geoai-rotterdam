"""Speelplekken binnen 100 m van een 50 km/u-weg in Rotterdam.

Ruimtelijke selectie + kaart: welke speelplekken liggen op ≤ 100 m van een weg met
maximumsnelheid 50 km/u? De ≤ 100 m-speelplekken worden rood uitgelicht, de overige
grijs, met het 50 km/u-wegennet als context. De volledige lijst wordt als CSV
weggeschreven naar de project-datamap.

Bronnen:
- Speelplekken: `SB_Infra/Speelplekken` (Obsurv / Gemeente Rotterdam), polygonen.
- Wegen: OpenStreetMap via Overpass (`maxspeed=50`), uit de project-cache
  `osm_wegen_rotterdam.json` (zie kaart_wegen_maxsnelheid_rotterdam.py).

Definitie "binnen 100 m": kortste afstand van het speelplek-vlak tot een 50 km/u-weg
≤ 100 m. Identificatie via SPEELPLEKCODE + STRAAT + WIJK (SPEELPLEKNAAM is rommelig).
"""

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import numpy as np
import geopandas as gpd
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    fetch_arcgis_layer, load_layer, style_map, add_scalebar,
    add_rotterdam_basemap, add_pdok_basemap, finalize_map, fit_figure_to_data,
    place_legend, save_map, setup_headless_matplotlib, CACHE, DATA_OUT, RD_NEW,
)

setup_headless_matplotlib()
AFSTAND_M = 100

# --- speelplekken (polygonen) -----------------------------------------------
sp_cache = os.path.join(str(CACHE), "speelplekken.geojson")
if os.path.exists(sp_cache):
    speel = gpd.read_file(sp_cache)
else:
    speel = fetch_arcgis_layer(
        "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Speelplekken/MapServer/0")
    speel.to_file(sp_cache, driver="GeoJSON")
speel = speel.to_crs(RD_NEW)
speel["geometry"] = speel.geometry.buffer(0)          # repareer invalide polygonen

# --- 50 km/u-wegen uit OSM-cache --------------------------------------------
gem = load_layer("gemeente").to_crs(RD_NEW)
data = json.load(open(os.path.join(str(CACHE), "osm_wegen_rotterdam.json"), encoding="utf-8"))


def parse_speed(v):
    m = re.match(r"(\d+)", str(v).strip().lower()) if v else None
    return int(m.group(1)) if m else None


rows = [{"geometry": LineString([(p["lon"], p["lat"]) for p in el["geometry"]])}
        for el in data.get("elements", [])
        if el.get("type") == "way" and "geometry" in el
        and parse_speed(el.get("tags", {}).get("maxspeed")) == 50
        and len(el["geometry"]) >= 2]
wegen50 = gpd.GeoDataFrame(rows, crs=4326).to_crs(RD_NEW)
wegen50 = gpd.clip(wegen50, gem)
wegen50 = wegen50[~wegen50.geometry.is_empty & wegen50.geometry.notna()]

# --- selectie: binnen 100 m -------------------------------------------------
near = gpd.sjoin_nearest(speel, wegen50[["geometry"]], max_distance=AFSTAND_M,
                         distance_col="afstand_m", how="inner")
near = near.sort_values("afstand_m").drop_duplicates(subset="ID")
near_ids = set(near["ID"])
speel["dichtbij"] = speel["ID"].isin(near_ids)
n_near = int(speel["dichtbij"].sum())
n_far = len(speel) - n_near
print(f"binnen {AFSTAND_M} m van een 50 km/u-weg: {n_near} van {len(speel)} "
      f"({n_near / len(speel) * 100:.0f}%)")

# CSV-export van de selectie
os.makedirs(str(DATA_OUT), exist_ok=True)
csv_cols = ["SPEELPLEKCODE", "STRAAT", "WIJK", "DOELGROEP", "afstand_m"]
csv = near[csv_cols].copy()
csv["afstand_m"] = csv["afstand_m"].round(1)
csv_path = os.path.join(str(DATA_OUT), "speelplekken_binnen100m_50weg.csv")
csv.to_csv(csv_path, index=False, encoding="utf-8-sig")
print("CSV:", csv_path)

# --- kaart ------------------------------------------------------------------
DICHT, VER, WEG = "#d73027", "#bdbdbd", "#8da0cb"
pt = speel.geometry.representative_point()
speel["x"], speel["y"] = pt.x.to_numpy(), pt.y.to_numpy()

fig, ax = plt.subplots(figsize=(13, 11))
gem.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=3)
wegen50.plot(ax=ax, color=WEG, linewidth=0.5, alpha=0.7, zorder=4)
ax.scatter(speel.loc[~speel["dichtbij"], "x"], speel.loc[~speel["dichtbij"], "y"],
           s=6, color=VER, zorder=5)
ax.scatter(speel.loc[speel["dichtbij"], "x"], speel.loc[speel["dichtbij"], "y"],
           s=15, color=DICHT, edgecolor="white", linewidths=0.2, zorder=6)

bron_delen = ["Speelplekken: Obsurv/Gemeente Rotterdam", "Wegen: OpenStreetMap (Overpass)"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as e:
    print("fallback PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "Speelplekken binnen 100 m van een 50 km/u-weg")
add_scalebar(ax, inside=True)
finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# legenda ná fit_figure_to_data (definitieve figuurhoogte -> correcte plaatsing);
# corner="auto" mijdt automatisch alle geplotte lagen (punten, wegen, gemeentegrens)
handles = [
    Line2D([0], [0], color=WEG, lw=2.0, label="50 km/u-weg"),
    Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=DICHT,
           markeredgecolor="white", markersize=8, label=f"Speelplek ≤ 100 m (n={n_near})"),
    Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=VER,
           markeredgecolor="none", markersize=6, label=f"Speelplek > 100 m (n={n_far})"),
]
place_legend(ax, handles=handles, corner="auto", title="Legenda")

print("opgeslagen:", save_map(fig, "speelplekken_binnen100m_50weg"))
