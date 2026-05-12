"""Interactieve kaart: lantaarnpalen binnen 10m van een afvalbak – Kralingen-Crooswijk."""

import json, ssl, math
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path

import geopandas as gpd
import folium
from folium.plugins import MarkerCluster

BASE  = Path("/Users/ds/Werk/GEOAI test/General data/Data")
OUT   = Path("/Users/ds/Werk/GEOAI test/output")
LICHT_URL = "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/LICHTPUNTEN/MapServer/0"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def fetch_json(url, params):
    with urlopen(f"{url}?{urlencode(params)}", context=CTX, timeout=60) as r:
        return json.loads(r.read().decode())

# ── 1. Kralingen buurten ──────────────────────────────────────────────────────
print("Buurten laden...")
buurten = gpd.read_file(BASE / "tir_buurten.geojson").set_crs(epsg=28992, allow_override=True)
kralingen = buurten[buurten["GEBDNAAM"] == "Kralingen-Crooswijk"].copy()
bbox = kralingen.total_bounds
bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"

# ── 2. Download lichtpunten ───────────────────────────────────────────────────
print("Lichtpunten downloaden...")
total = fetch_json(f"{LICHT_URL}/query", {
    "where": "1=1", "geometry": bbox_str,
    "geometryType": "esriGeometryEnvelope", "inSR": "28992",
    "returnCountOnly": "true", "f": "json",
})["count"]

features = []
for offset in range(0, total, 1000):
    data = fetch_json(f"{LICHT_URL}/query", {
        "where": "1=1", "geometry": bbox_str,
        "geometryType": "esriGeometryEnvelope", "inSR": "28992",
        "outFields": "*", "returnGeometry": "true", "outSR": "28992",
        "resultOffset": str(offset), "resultRecordCount": "1000", "f": "geojson",
    })
    features.extend(data.get("features", []))
    print(f"  batch {offset//1000+1}/{math.ceil(total/1000)}")

licht_all = gpd.GeoDataFrame.from_features(features, crs="EPSG:28992")
licht_k = gpd.sjoin(licht_all, kralingen[["BUURTNAAM", "geometry"]], how="inner", predicate="within").drop(columns="index_right", errors="ignore")
print(f"  {len(licht_k)} lichtpunten in Kralingen")

# ── 3. Afvalbakken ────────────────────────────────────────────────────────────
print("Afvalbakken laden...")
afval = gpd.read_file(BASE / "afvalbak.geojson").set_crs(epsg=28992, allow_override=True)
afval_k = gpd.sjoin(afval, kralingen[["BUURTNAAM", "geometry"]], how="inner", predicate="within")
print(f"  {len(afval_k)} afvalbakken in Kralingen")

# ── 4. Proximity: buffer 10m ─────────────────────────────────────────────────
afval_buffer = afval_k.copy()
afval_buffer["geometry"] = afval_k.geometry.buffer(10)

licht_bij_afval = gpd.sjoin(licht_k, afval_buffer[["STRAAT", "TYPE", "geometry"]], how="inner", predicate="within")
licht_bij_afval = licht_bij_afval[~licht_bij_afval.index.duplicated()]
licht_ver = licht_k[~licht_k.index.isin(licht_bij_afval.index)]

print(f"\nResultaat:")
print(f"  Binnen 10m: {len(licht_bij_afval)} ({len(licht_bij_afval)/len(licht_k)*100:.1f}%)")
print(f"  Verder:     {len(licht_ver)}")

# ── 5. Reproject naar WGS84 ──────────────────────────────────────────────────
kralingen_wgs = kralingen.to_crs(epsg=4326)
afval_wgs = afval_k.to_crs(epsg=4326)
licht_bij_wgs = licht_bij_afval.to_crs(epsg=4326)
licht_ver_wgs = licht_ver.to_crs(epsg=4326)

centroid = kralingen_wgs.union_all().centroid
center = [centroid.y, centroid.x]

# ── 6. Folium kaart ──────────────────────────────────────────────────────────
print("Kaart opbouwen...")
m = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron")

# Buurtgrenzen
for _, row in kralingen_wgs.iterrows():
    folium.GeoJson(
        row["geometry"].__geo_interface__,
        style_function=lambda f: {
            "fillColor": "#f5f0e8", "color": "#333333",
            "weight": 1.5, "fillOpacity": 0.3,
        },
        tooltip=row["BUURTNAAM"],
    ).add_to(m)

# Grijze lantaarnpalen (verder dan 10m) — als FeatureGroup zodat je kunt togglen
fg_ver = folium.FeatureGroup(name=f"Verder dan 10m ({len(licht_ver_wgs)})", show=True)
for _, row in licht_ver_wgs.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=2, color="#aaaaaa", fill=True, fill_opacity=0.4, weight=0,
    ).add_to(fg_ver)
fg_ver.add_to(m)

# Afvalbakken
fg_afval = folium.FeatureGroup(name=f"Afvalbakken ({len(afval_wgs)})", show=True)
for _, row in afval_wgs.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=4, color="#c0392b", fill=True, fill_color="#c0392b",
        fill_opacity=0.7, weight=1,
        popup=folium.Popup(
            f"<b>Afvalbak</b><br>Type: {row.get('TYPE','—')}<br>Straat: {row.get('STRAAT','—')}",
            max_width=200,
        ),
    ).add_to(fg_afval)
fg_afval.add_to(m)

# Oranje lantaarnpalen (binnen 10m) — BOVENSTE laag
fg_binnen = folium.FeatureGroup(name=f"Binnen 10m van afvalbak ({len(licht_bij_wgs)})", show=True)
for _, row in licht_bij_wgs.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=6, color="#e67e22", fill=True, fill_color="#e67e22",
        fill_opacity=0.9, weight=1.5,
        popup=folium.Popup(
            f"<b>Lantaarnpaal binnen 10m</b><br>"
            f"Buurt: {row.get('BUURTNAAM','—')}",
            max_width=200,
        ),
    ).add_to(fg_binnen)
fg_binnen.add_to(m)

# Legenda
legend_html = f"""
<div style="position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
     padding:14px 18px;border-radius:8px;box-shadow:2px 2px 8px rgba(0,0,0,0.3);
     font-family:sans-serif;font-size:13px;min-width:230px">
  <b style="font-size:14px">Kralingen-Crooswijk</b><br>
  <span style="color:#666;font-size:11px">Lantaarnpalen &lt;10m van afvalbak</span>
  <hr style="margin:6px 0">
  <div style="margin:4px 0">
    <span style="display:inline-block;width:14px;height:14px;
    background:#e67e22;border-radius:50%;margin-right:8px;vertical-align:middle"></span>
    Binnen 10m <b>({len(licht_bij_wgs)})</b> — {len(licht_bij_wgs)/len(licht_k)*100:.1f}%
  </div>
  <div style="margin:4px 0">
    <span style="display:inline-block;width:10px;height:10px;
    background:#aaaaaa;border-radius:50%;margin-right:10px;vertical-align:middle"></span>
    Verder dan 10m <b>({len(licht_ver_wgs)})</b>
  </div>
  <div style="margin:4px 0">
    <span style="display:inline-block;width:10px;height:10px;
    background:#c0392b;border-radius:50%;margin-right:10px;vertical-align:middle"></span>
    Afvalbakken <b>({len(afval_wgs)})</b>
  </div>
  <hr style="margin:6px 0">
  <span style="color:#666;font-size:11px">Klik op een oranje punt voor details</span>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
folium.LayerControl(collapsed=False).add_to(m)

# ── Opslaan ───────────────────────────────────────────────────────────────────
out = OUT / "kralingen_licht_bij_afval.html"
m.save(str(out))
print(f"\nOpgeslagen: {out}")
