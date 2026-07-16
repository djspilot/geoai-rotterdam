"""
Kaart: Lichtpunten in Stadsdriehoek (Centrum), Rotterdam
Download via ArcGIS REST + statische kaart met matplotlib/geopandas
"""

import sys
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "General data"))
from rotterdam import style_map, finalize_map, place_legend, save_map, validate_map

DATA = ROOT / "General data" / "Data"

# --- 1. Download lichtpunten voor Stadsdriehoek ---
base_url = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/LICHTPUNTEN/MapServer/0/query"
batch_size = 2000
offset = 0
all_features = []

print("Downloading lichtpunten voor Stadsdriehoek...")

while True:
    params = {
        "where": "WIJK='Stadsdriehoek'",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "28992",
        "resultOffset": str(offset),
        "resultRecordCount": str(batch_size),
        "f": "geojson",
    }
    url = f"{base_url}?{urlencode(params)}"
    resp = requests.get(url, verify=False)
    data = resp.json()

    features = data.get("features", [])
    if not features:
        break

    all_features.extend(features)
    print(f"  Batch offset {offset}: {len(features)} features")
    offset += batch_size

    if not data.get("exceededTransferLimit", False) and len(features) < batch_size:
        break

print(f"Totaal: {len(all_features)} lichtpunten gedownload")

# Maak GeoDataFrame
geojson = {"type": "FeatureCollection", "features": all_features}
lichtpunten = gpd.GeoDataFrame.from_features(geojson, crs="EPSG:28992")

# Sla op als GeoJSON voor hergebruik
lichtpunten.to_file(DATA / "lichtpunten_stadsdriehoek.geojson", driver="GeoJSON")
print(f"Opgeslagen als {DATA / 'lichtpunten_stadsdriehoek.geojson'}")

# --- 2. Laad TIR buurten voor de achtergrond ---
buurten = gpd.read_file(DATA / "tir_buurten.geojson")
if buurten.crs is None:
    buurten = buurten.set_crs(epsg=28992)
elif buurten.crs.to_epsg() != 28992:
    buurten = buurten.to_crs(epsg=28992)

# Filter buurten in Stadsdriehoek (gebied = Centrum)
stadsdriehoek = buurten[buurten["BUURTNAAM"].str.contains("Stadsdriehoek", case=False, na=False)]
if stadsdriehoek.empty:
    # Probeer via GEBDNAAM
    centrum = buurten[buurten["GEBDNAAM"].str.contains("Centrum", case=False, na=False)]
    print(f"Geen buurt 'Stadsdriehoek' gevonden, gebruik Centrum gebied ({len(centrum)} buurten)")
    stadsdriehoek = centrum

# Union van de buurten als achtergrond
buurt_boundary = stadsdriehoek.dissolve()

# --- 3. Statische kaart ---
fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Buurt achtergrond
buurt_boundary.plot(ax=ax, color="#f0f0f0", edgecolor="#333333", linewidth=1.5)
stadsdriehoek.plot(ax=ax, facecolor="none", edgecolor="#999999", linewidth=0.5, linestyle="--")

# Kleur op basis van LICHTPUNTTYPE als dat bestaat
if "LICHTPUNTTYPE" in lichtpunten.columns:
    types = lichtpunten["LICHTPUNTTYPE"].fillna("Onbekend").unique()
    cmap = plt.colormaps.get_cmap("Set2").resampled(len(types))
    for i, ltype in enumerate(sorted(types)):
        subset = lichtpunten[lichtpunten["LICHTPUNTTYPE"].fillna("Onbekend") == ltype]
        subset.plot(ax=ax, markersize=5, color=cmap(i), alpha=0.7, label=ltype)
else:
    lichtpunten.plot(ax=ax, markersize=5, color="#e74c3c", alpha=0.6, label="Lichtpunt")

ax.set_aspect("equal")

# Voeg buurt labels toe
for _, row in stadsdriehoek.iterrows():
    if row.geometry is None or row.geometry.is_empty:
        continue
    centroid = row.geometry.centroid
    if centroid.is_empty:
        continue
    label = row.get("BUURTNAAM", "")
    if label:
        ax.annotate(label, xy=(centroid.x, centroid.y), fontsize=5,
                    ha="center", va="center", color="#555555")

# Kaartelementen + footer via de library (conventies)
style_map(ax, "Lichtpunten in Stadsdriehoek (Centrum)",
          subtitle=f"{len(lichtpunten)} lichtpunten")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl")
_handles, _labels = ax.get_legend_handles_labels()
if _handles:
    place_legend(ax, _handles, _labels, title="Lichtpunttype", corner="auto",
                 data=lichtpunten)

warns = validate_map(fig, ax, data=lichtpunten)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out = save_map(fig, "kaart_lichtpunten_stadsdriehoek")
print(f"Kaart opgeslagen: {out}")
