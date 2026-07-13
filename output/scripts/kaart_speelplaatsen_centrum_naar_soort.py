"""Speelplaatsen in Rotterdam Centrum, geclassificeerd naar soort (DOELGROEP).

Genummerde index-kaart:
- vlakken gekleurd per soort (Sport- en Speel, Speelplekje, Pocketpark, ...),
- elke speelplek een uniek nummer (1..N, van noord naar zuid),
- nummer buiten het object (45 graden rechtsboven; bij overlap met de klok mee
  een vrije plek zoeken) met een leader line, zodat de vlakken/kleuren zichtbaar
  blijven; grote objecten krijgen het nummer erop,
- genummerde namenlijst rechtsonder, soort-legenda rechtsboven,
- Rotterdamse kleur-basemap (met PDOK-fallback).

Bron: Obsurv via diensten.rotterdam.nl (laag SB_Infra/Speelplekken).
"""

import os
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from sklearn.cluster import DBSCAN  # noqa: F401  (kan handig zijn voor varianten)

from rotterdam import (
    load_layer, fetch_arcgis_layer, style_map, add_scalebar,
    add_rotterdam_basemap, add_pdok_basemap, finalize_map, fit_figure_to_data,
    add_side_panel, save_map, setup_headless_matplotlib, RD_NEW, CACHE,
)

setup_headless_matplotlib()

SPEEL_URL = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Speelplekken/MapServer/0"
CACHE_FILE = os.path.join(str(CACHE), "speelplekken.geojson")
HALO = [pe.withStroke(linewidth=1.8, foreground="white")]
KLEUREN = {
    "Sport- en Speel": "#1f77b4", "Speelplekje": "#ff7f0e", "Pocketpark": "#2ca02c",
    "Centrale Ontmoe": "#9467bd", "Restruimte": "#8c564b", "Onbekend": "#999999",
}


def short(s, n=30):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


# --- data (met cache) ---
if os.path.exists(CACHE_FILE):
    speel = gpd.read_file(CACHE_FILE)
else:
    os.makedirs(str(CACHE), exist_ok=True)
    fc = fetch_arcgis_layer(SPEEL_URL)
    speel = gpd.GeoDataFrame.from_features(fc["features"], crs=RD_NEW)
    speel.to_file(CACHE_FILE, driver="GeoJSON")

gebieden = load_layer("gebieden")
centrum = gebieden[gebieden["GEBDNAAM"] == "Rotterdam Centrum"]
speel_c = speel[speel.intersects(centrum.geometry.iloc[0])].copy()
speel_c["pt"] = speel_c.geometry.representative_point()
speel_c["rx"] = speel_c["pt"].x
speel_c["ry"] = speel_c["pt"].y
speel_c["naam"] = speel_c["SPEELPLEKNAAM"].fillna("(naamloos)")
speel_c["SOORT"] = speel_c["DOELGROEP"].fillna("Onbekend")
speel_c = speel_c.sort_values("ry", ascending=False).reset_index(drop=True)
speel_c["nr"] = range(1, len(speel_c) + 1)

# --- tekenen ---
fig, ax = plt.subplots(figsize=(11, 11))   # hoogte wordt later door fit_figure_to_data bijgesteld
centrum.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=4)
order = [s for s in KLEUREN if s in set(speel_c["SOORT"])]
for soort in order:
    sub = speel_c[speel_c["SOORT"] == soort]
    sub.plot(ax=ax, facecolor=KLEUREN[soort], edgecolor="white", linewidth=0.4, alpha=0.9, zorder=6)

# basemap: Rotterdam kleur, val terug op PDOK als de server niet reageert
try:
    add_rotterdam_basemap(ax, layer="kleur")
    basiskaart = "Basiskaart: Gemeente Rotterdam (kleur)"
except Exception as e:
    print("Rotterdam-basemap faalde, val terug op PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    basiskaart = "Basiskaart: PDOK BRT"


def draw_num(nr, xy, xytext=None):
    if xytext is None:
        t = ax.text(xy[0], xy[1], str(nr), ha="center", va="center",
                    fontsize=7.5, fontweight="bold", color="black", zorder=11)
    else:
        t = ax.annotate(str(nr), xy=xy, xytext=xytext, textcoords="data",
                        ha="center", va="center", fontsize=7.5, fontweight="bold",
                        color="black", zorder=11,
                        arrowprops=dict(arrowstyle="-", lw=1.1, color="#111111",
                                        shrinkA=1, shrinkB=2.5))
    t.set_path_effects(HALO)


# label-plaatsing: klein object -> nummer buiten (45 graden rechtsboven), bij
# overlap met de klok mee draaien; groot object -> nummer erop.
x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
W, H = x1 - x0, y1 - y0
ZONES = []   # legenda en lijst staan in het paneel naast de kaart, niet erop


def in_zone(fx, fy):
    return any(a <= fx <= c and b <= fy <= d for a, b, c, d in ZONES)


LABEL_W, LABEL_H, GAP = 44, 28, 22
CW = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]  # met de klok mee vanaf rechtsboven


def box_at(cx, cy):
    return (cx - LABEL_W / 2, cy - LABEL_H / 2, cx + LABEL_W / 2, cy + LABEL_H / 2)


def boxes_overlap(a, b):
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def spot_ok(cx, cy):
    fx, fy = (cx - x0) / W, (cy - y0) / H
    return 0.02 < fx < 0.98 and 0.02 < fy < 0.98 and not in_zone(fx, fy)


obst = speel_c.geometry.bounds[["minx", "miny", "maxx", "maxy"]].values
placed = []
for idx, r in speel_c.iterrows():
    rx, ry = r["rx"], r["ry"]
    minx, miny, maxx, maxy = obst[idx]
    bw, bh = maxx - minx, maxy - miny
    obscured = min(bw, bh) < 45 or max(bw, bh) < 75     # nummer zou 't object verhullen
    chosen, leader = None, False

    if not obscured and not any(boxes_overlap(box_at(rx, ry), p) for p in placed):
        chosen = (rx, ry)

    if chosen is None:
        base = 0.5 * max(bw, bh) + GAP + max(LABEL_W, LABEL_H) / 2
        for scale in (1.0, 1.7, 2.5, 3.3):
            for ux, uy in CW:
                n = (ux * ux + uy * uy) ** 0.5
                cx, cy = rx + ux / n * base * scale, ry + uy / n * base * scale
                if not spot_ok(cx, cy):
                    continue
                lb = box_at(cx, cy)
                if any(boxes_overlap(lb, obst[j]) for j in range(len(obst))):
                    continue
                if any(boxes_overlap(lb, p) for p in placed):
                    continue
                chosen, leader = (cx, cy), True
                break
            if chosen is not None:
                break
        if chosen is None:
            chosen, leader = (rx + 0.707 * base, ry + 0.707 * base), True

    draw_num(r["nr"], (rx, ry), xytext=chosen if leader else None)
    placed.append(box_at(*chosen))

style_map(ax, "Speelplaatsen in het stadscentrum van Rotterdam — naar soort")
add_scalebar(ax, inside=True)

finalize_map(fig, source=f"Obsurv via diensten.rotterdam.nl · {basiskaart}",
             tight_bottom=True)               # schaalstok staat in de kaart
fit_figure_to_data(fig, ax)                    # figuurhoogte op de gebiedsvorm

# --- legenda + genummerde namenlijst in een PANEEL naast de kaart (niet erop) ---
panel = add_side_panel(fig, ax, width_in=3.6)

# soort-legenda bovenin het paneel
handles = [Patch(facecolor=KLEUREN[s], edgecolor="white",
                 label=f"{s} ({(speel_c['SOORT'] == s).sum()})") for s in order]
pleg = panel.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.04, 0.99),
                    borderaxespad=0, title="Legenda", frameon=False, fontsize=9)
pleg.set_alignment("left")
pleg.get_title().set_fontweight("bold")

# 'Naam'-lijst onder de legenda: nummers rechts uitgelijnd, namen links ernaast
fig.canvas.draw()
leg_b = pleg.get_window_extent(fig.canvas.get_renderer()).transformed(
    panel.transAxes.inverted()).y0
yt = leg_b - 0.03
panel.text(0.04, yt, "Naam", transform=panel.transAxes, ha="left", va="top",
           fontsize=10, fontweight="bold")
nums = "\n".join(f"{r['nr']:d}" for _, r in speel_c.iterrows())
names = "\n".join(short(r["naam"]) for _, r in speel_c.iterrows())
yl = yt - 0.028
panel.text(0.11, yl, nums, transform=panel.transAxes, ha="right", va="top",
           ma="right", fontsize=8, linespacing=1.35)
panel.text(0.13, yl, names, transform=panel.transAxes, ha="left", va="top",
           ma="left", fontsize=8, linespacing=1.35)

out = save_map(fig, "speelplaatsen_centrum_naar_soort")
print(f"Speelplaatsen in Centrum: {len(speel_c)}")
print(f"SAVED: {out}")
