"""Statische kaart: Kralingen-Crooswijk met afvalbakken én lantaarnpalen."""

import json, ssl, math
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import shape

BASE  = Path("/Users/ds/Werk/GEOAI test/General data/Data")
OUT   = Path("/Users/ds/Werk/GEOAI test/output")
LICHT_URL = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/LICHTPUNTEN/MapServer/0"

# ── SSL context ───────────────────────────────────────────────────────────────
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def fetch_json(url, params):
    with urlopen(f"{url}?{urlencode(params)}", context=CTX, timeout=60) as r:
        return json.loads(r.read().decode())

# ── 1. Laad Kralingen buurten ─────────────────────────────────────────────────
print("Buurten laden...")
buurten = gpd.read_file(BASE / "tir_buurten.geojson").set_crs(epsg=28992, allow_override=True)
kralingen = buurten[buurten["GEBDNAAM"] == "Kralingen-Crooswijk"].copy()

# Bounding box van Kralingen in RD New voor spatiale filter
bbox = kralingen.total_bounds  # [minx, miny, maxx, maxy]
bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

# ── 2. Download lichtpunten binnen Kralingen bbox ─────────────────────────────
print("Lichtpunten downloaden (binnen Kralingen bbox)...")
count_r = fetch_json(f"{LICHT_URL}/query", {
    "where": "1=1", "geometry": bbox_str,
    "geometryType": "esriGeometryEnvelope", "inSR": "28992",
    "returnCountOnly": "true", "f": "json",
})
total = int(count_r.get("count", 0))
print(f"  {total} lichtpunten in bbox")

features = []
batch = 1000
for offset in range(0, total, batch):
    data = fetch_json(f"{LICHT_URL}/query", {
        "where": "1=1",
        "geometry": bbox_str,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "28992",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "28992",
        "resultOffset": str(offset),
        "resultRecordCount": str(batch),
        "f": "geojson",
    })
    features.extend(data.get("features", []))
    print(f"  batch {offset//batch+1}/{math.ceil(total/batch)}: {len(data.get('features',[]))} features")

licht_gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:28992")
print(f"  Totaal geladen: {len(licht_gdf)}")

# ── 3. Laad afvalbakken ───────────────────────────────────────────────────────
print("Afvalbakken laden...")
afval = gpd.read_file(BASE / "afvalbak.geojson").set_crs(epsg=28992, allow_override=True)

# ── 4. Spatial join naar Kralingen buurten ────────────────────────────────────
licht_k  = gpd.sjoin(licht_gdf, kralingen[["BUURTNAAM","geometry"]], how="inner", predicate="within")
afval_k  = gpd.sjoin(afval,     kralingen[["BUURTNAAM","geometry"]], how="inner", predicate="within")
print(f"Lichtpunten in Kralingen: {len(licht_k)}")
print(f"Afvalbakken in Kralingen: {len(afval_k)}")

# ── 5. Kleuren per buurt ──────────────────────────────────────────────────────
KLEUREN = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e"]
buurt_namen = sorted(kralingen["BUURTNAAM"].unique())
kleur_map = {n: KLEUREN[i % len(KLEUREN)] for i, n in enumerate(buurt_namen)}
kralingen = kralingen.copy()
kralingen["kleur"] = kralingen["BUURTNAAM"].map(kleur_map)

# ── 6. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 12))

# Buurt vlakken
for _, row in kralingen.iterrows():
    gpd.GeoDataFrame([row], crs=kralingen.crs).plot(
        ax=ax, color=row["kleur"], edgecolor="#333333", linewidth=1.5, alpha=0.2)

# Lantaarnpalen (geel, klein)
for buurt_naam in buurt_namen:
    sub = licht_k[licht_k["BUURTNAAM"] == buurt_naam]
    ax.scatter(sub.geometry.x, sub.geometry.y,
               color="#f1c40f", s=4, alpha=0.6, zorder=3, marker="^")

# Afvalbakken (buurtkleur, iets groter)
for buurt_naam in buurt_namen:
    sub = afval_k[afval_k["BUURTNAAM"] == buurt_naam]
    ax.scatter(sub.geometry.x, sub.geometry.y,
               color=kleur_map[buurt_naam], s=14, alpha=0.85, zorder=4)

# Buurtgrenzen bovenop
kralingen.boundary.plot(ax=ax, color="#333333", linewidth=1.5, zorder=5)

# Labels
for _, row in kralingen.iterrows():
    cx = row.geometry.centroid.x
    cy = row.geometry.centroid.y
    nl = len(licht_k[licht_k["BUURTNAAM"] == row["BUURTNAAM"]])
    na = len(afval_k[afval_k["BUURTNAAM"] == row["BUURTNAAM"]])
    ax.annotate(
        f"{row['BUURTNAAM']}\n▲{nl}  ●{na}",
        xy=(cx, cy), ha="center", va="center",
        fontsize=7.5, fontweight="bold", color="#111111",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.75, ec="none"),
        zorder=6,
    )

# Legenda
patches = [mpatches.Patch(color=k, label=n) for n, k in kleur_map.items()]
patches += [
    mpatches.Patch(color="#f1c40f", label=f"▲ Lantaarnpalen  (totaal {len(licht_k)})"),
    mpatches.Patch(color="#888888", label=f"● Afvalbakken  (totaal {len(afval_k)})"),
]
ax.legend(handles=patches, title="Legenda", loc="lower right",
          fontsize=8, title_fontsize=9, framealpha=0.9, edgecolor="#cccccc")

ax.set_title("Lantaarnpalen & Afvalbakken – Kralingen-Crooswijk", fontsize=14, pad=14)
ax.set_axis_off()
plt.tight_layout()

out = OUT / "kralingen_lantaarnpalen.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nOpgeslagen: {out}")
