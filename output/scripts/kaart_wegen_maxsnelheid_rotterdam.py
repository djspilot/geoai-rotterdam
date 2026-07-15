"""Wegen in Rotterdam geclassificeerd naar maximale snelheid.

Alle autowegen binnen de gemeentegrens (motorway t/m living_street) uit
OpenStreetMap, geclassificeerd naar hun `maxspeed`-tag. Kleurverloop groen->rood
(langzaam->snel) en oplopende lijndikte, zodat woonstraten (30/50) rustig blijven
en snelwegen (A15/A20/A4, >=120) er duidelijk uitspringen.

Databron: OpenStreetMap via de Overpass API — een gedocumenteerde nationale bron
in de skill (`national_sources.md`). De ruwe respons wordt in de project-cache
bewaard, zodat herhaald draaien Overpass niet opnieuw belast. Wegen worden op de
gemeentegrens (`load_layer("gemeente")`) geknipt.

Bron: OpenStreetMap (Overpass) · © OpenStreetMap-bijdragers.
"""

import os
import re
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, style_map, add_scalebar, add_rotterdam_basemap, add_pdok_basemap,
    finalize_map, fit_figure_to_data, place_legend, save_map,
    setup_headless_matplotlib, RD_NEW, CACHE,
)

setup_headless_matplotlib()

# --- data: OSM autowegen binnen de Rotterdamse bbox -------------------------
gemeente = load_layer("gemeente").to_crs(RD_NEW)
w, s, e, n = gemeente.to_crs(4326).total_bounds

road_re = ("^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|"
           "secondary|secondary_link|tertiary|tertiary_link|unclassified|"
           "residential|living_street)$")
query = f"""[out:json][timeout:240];
way["highway"~"{road_re}"]({s},{w},{n},{e});
out geom;"""

os.makedirs(CACHE, exist_ok=True)
cache_file = os.path.join(CACHE, "osm_wegen_rotterdam.json")
if os.path.exists(cache_file):
    data = json.load(open(cache_file, encoding="utf-8"))
else:
    req = urllib.request.Request("https://overpass-api.de/api/interpreter",
                                 data=query.encode("utf-8"),
                                 headers={"User-Agent": "geoai-rotterdam/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=300).read().decode("utf-8"))
    json.dump(data, open(cache_file, "w", encoding="utf-8"))


def parse_speed(v):
    if not v:
        return None
    v = str(v).strip().lower()
    if v in ("none", "signals", "variable", "walk"):
        return None
    m = re.match(r"(\d+)", v)
    return int(m.group(1)) if m else None


rows = []
for el in data.get("elements", []):
    if el.get("type") != "way" or "geometry" not in el:
        continue
    coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
    if len(coords) < 2:
        continue
    rows.append({"maxspeed": parse_speed(el.get("tags", {}).get("maxspeed")),
                 "geometry": LineString(coords)})

roads = gpd.GeoDataFrame(rows, crs=4326).to_crs(RD_NEW)
roads = gpd.clip(roads, gemeente)
roads = roads[~roads.geometry.is_empty & roads.geometry.notna()]
print(f"wegen in Rotterdam: {len(roads):,}")


def bucket(sp):
    if sp is None:
        return "onbekend"
    if sp <= 30:
        return "≤ 30 km/u"
    if sp <= 50:
        return "50 km/u"
    if sp <= 70:
        return "60–70 km/u"
    if sp <= 80:
        return "80 km/u"
    if sp <= 100:
        return "90–100 km/u"
    return "≥ 120 km/u"


roads["klasse"] = roads["maxspeed"].apply(bucket)
print(roads["klasse"].value_counts())

CLASSES = ["≤ 30 km/u", "50 km/u", "60–70 km/u", "80 km/u",
           "90–100 km/u", "≥ 120 km/u", "onbekend"]
COLORS = {
    "≤ 30 km/u": "#1a9850", "50 km/u": "#91cf60", "60–70 km/u": "#fee08b",
    "80 km/u": "#fc8d59", "90–100 km/u": "#d73027", "≥ 120 km/u": "#7f0000",
    "onbekend": "#bdbdbd",
}
LW = {
    "≤ 30 km/u": 0.5, "50 km/u": 0.7, "60–70 km/u": 0.9, "80 km/u": 1.2,
    "90–100 km/u": 1.5, "≥ 120 km/u": 1.8, "onbekend": 0.4,
}

# --- kaart ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 11))
gemeente.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=3)
# onbekend onderop, dan oplopend zodat snellere wegen bovenop liggen
for cls in ["onbekend"] + CLASSES[:-1]:
    sub = roads[roads["klasse"] == cls]
    if len(sub):
        sub.plot(ax=ax, color=COLORS[cls], linewidth=LW[cls],
                 zorder=5 + CLASSES.index(cls))

# invariant 10 staat afwijken toe als kleur de data onleesbaar maakt: op de
# kleur-basemap vochten de groene 30/50-wegen met groene parken en botste het
# dubbele wegennet. Grijs geeft een neutrale onderlaag waarop de snelheidskleuren
# dragen. Invariant 12: eigen Rotterdam-basemap niet vermelden, derde-partij wel.
bron_delen = ["OpenStreetMap (Overpass)"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as ex:
    print("fallback PDOK:", type(ex).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "Wegen in Rotterdam naar maximale snelheid")
# geen schaalstok: thematische kaart, afstand niet relevant (invariant 14)
finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# legenda ná fit_figure_to_data plaatsen: dan is de figuurhoogte (en dus de
# legendagrootte) definitief en klopt de auto-plaatsing met de uiteindelijke kaart
present = [c for c in CLASSES if (roads["klasse"] == c).any()]
handles = [Line2D([0], [0], color=COLORS[c], lw=max(LW[c], 2.0), label=c)
           for c in present]
place_legend(ax, handles=handles, corner="auto", title="Max. snelheid")

print("opgeslagen:", save_map(fig, "wegen_maxsnelheid_rotterdam"))
