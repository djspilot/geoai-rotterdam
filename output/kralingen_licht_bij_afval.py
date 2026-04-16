"""Kaart: lantaarnpalen binnen 10m van een afvalbak in Kralingen-Crooswijk."""

import json, ssl, math
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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

licht_all = gpd.GeoDataFrame.from_features(features, crs="EPSG:28992")
licht_k = gpd.sjoin(licht_all, kralingen[["BUURTNAAM", "geometry"]], how="inner", predicate="within").drop(columns="index_right")
print(f"  {len(licht_k)} lichtpunten in Kralingen")

# ── 3. Afvalbakken ────────────────────────────────────────────────────────────
afval = gpd.read_file(BASE / "afvalbak.geojson").set_crs(epsg=28992, allow_override=True)
afval_k = gpd.sjoin(afval, kralingen[["BUURTNAAM", "geometry"]], how="inner", predicate="within").drop(columns="index_right")
print(f"  {len(afval_k)} afvalbakken in Kralingen")

# ── 4. Analyse: lichtpunten binnen 10m van een afvalbak ──────────────────────
afval_buffer = afval_k.copy()
afval_buffer["geometry"] = afval_k.geometry.buffer(10)  # 10 meter (RD New = metrisch)

# Spatial join: welke lantaarnpalen vallen binnen een buffer?
match_idx = gpd.sjoin(licht_k[["geometry"]], afval_buffer[["geometry"]], how="inner", predicate="within").index.unique()
licht_bij_afval = licht_k.loc[licht_k.index.isin(match_idx)]

licht_ver = licht_k[~licht_k.index.isin(licht_bij_afval.index)]

print(f"\nResultaat:")
print(f"  Lantaarnpalen BINNEN 10m van afvalbak : {len(licht_bij_afval)} ({len(licht_bij_afval)/len(licht_k)*100:.1f}%)")
print(f"  Lantaarnpalen VERDER dan 10m          : {len(licht_ver)}")

# ── 5. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 12))

# Buurt vlakken
kralingen.plot(ax=ax, color="#f5f0e8", edgecolor="#555555", linewidth=1.5, alpha=0.8)

# Afvalbak buffers (lichte achtergrond)
afval_buffer.plot(ax=ax, color="#e74c3c", alpha=0.07, zorder=2)

# Alle lantaarnpalen (grijs) — onderste laag
ax.scatter(licht_ver.geometry.x, licht_ver.geometry.y,
           color="#aaaaaa", s=4, alpha=0.5, zorder=3)

# Afvalbakken — middenlaag
ax.scatter(afval_k.geometry.x, afval_k.geometry.y,
           color="#c0392b", s=16, marker="s", alpha=0.7, zorder=4)

# Lantaarnpalen binnen 10m (oranje) — BOVENSTE laag, groter en opvallend
ax.scatter(licht_bij_afval.geometry.x, licht_bij_afval.geometry.y,
           color="#e67e22", s=30, alpha=1.0, zorder=6,
           edgecolors="#ffffff", linewidths=0.5)

# Buurtgrenzen
kralingen.boundary.plot(ax=ax, color="#333333", linewidth=1.5, zorder=7)

# Buurtnamen met aantallen
for _, row in kralingen.iterrows():
    buurt = row["BUURTNAAM"]
    n_binnen = len(licht_bij_afval[licht_bij_afval["BUURTNAAM"] == buurt])
    n_licht  = len(licht_k[licht_k["BUURTNAAM"] == buurt])
    n_afval  = len(afval_k[afval_k["BUURTNAAM"] == buurt])
    pct = (n_binnen / n_licht * 100) if n_licht > 0 else 0
    ax.annotate(
        f"{buurt}\n"
        f"● {n_binnen}/{n_licht} lantaarnp. ({pct:.0f}%)\n"
        f"■ {n_afval} afvalbak.",
        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
        ha="center", va="center", fontsize=6.5, fontweight="bold", color="#222222",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8, ec="#cccccc", lw=0.5),
        zorder=8,
    )

# Legenda — binnen 10m bovenaan
import matplotlib.lines as mlines
h_binnen = mlines.Line2D([], [], color="#e67e22", marker="o", linestyle="None",
                          markersize=7, label=f"Binnen 10m van afvalbak  ({len(licht_bij_afval)})")
h_ver    = mlines.Line2D([], [], color="#aaaaaa", marker="o", linestyle="None",
                          markersize=5, label=f"Verder dan 10m  ({len(licht_ver)})")
h_afval  = mlines.Line2D([], [], color="#c0392b", marker="s", linestyle="None",
                          markersize=6, label=f"Afvalbakken  ({len(afval_k)})")
ax.legend(handles=[h_binnen, h_ver, h_afval],
          loc="lower right", fontsize=9, framealpha=0.92, edgecolor="#cccccc")
ax.set_title(
    f"Lantaarnpalen binnen 10m van een afvalbak – Kralingen-Crooswijk\n"
    f"{len(licht_bij_afval)} van {len(licht_k)} lantaarnpalen ({len(licht_bij_afval)/len(licht_k)*100:.1f}%)",
    fontsize=13, pad=14,
)
ax.set_axis_off()
plt.tight_layout()

out = OUT / "kralingen_licht_bij_afval.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nOpgeslagen: {out}")
