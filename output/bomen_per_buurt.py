"""Bomen per buurt - choropleth kaart (statisch + interactief)."""

import glob
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from pathlib import Path

BASE = Path("/Users/ds/Werk/GEOAI test/General data/Data")
OUT  = Path("/Users/ds/Werk/GEOAI test/output")

# ── 1. Laad buurten ──────────────────────────────────────────────────────────
print("Buurten laden...")
buurten = gpd.read_file(BASE / "tir_buurten.geojson").set_crs(epsg=28992, allow_override=True)

# ── 2. Laad alle bomen chunks ─────────────────────────────────────────────────
print("Bomen laden (alle chunks)...")
chunks = sorted(glob.glob(str(BASE / "bomen_chunks" / "*.geojson")))
bomen = pd.concat([gpd.read_file(c) for c in chunks], ignore_index=True)
bomen = gpd.GeoDataFrame(bomen, geometry="geometry", crs="EPSG:28992")
print(f"  {len(bomen):,} bomen geladen uit {len(chunks)} chunks")

# ── 3. Spatial join: boom → buurt ─────────────────────────────────────────────
print("Spatial join uitvoeren...")
joined = gpd.sjoin(bomen[["geometry"]], buurten[["BUURTNAAM", "GEBDNAAM", "geometry"]],
                   how="inner", predicate="within")
counts = joined.groupby("BUURTNAAM").size().reset_index(name="aantal_bomen")
buurten = buurten.merge(counts, on="BUURTNAAM", how="left")
buurten["aantal_bomen"] = buurten["aantal_bomen"].fillna(0).astype(int)

top10 = buurten.nlargest(10, "aantal_bomen")[["BUURTNAAM", "GEBDNAAM", "aantal_bomen"]]
print("\nTop 10 buurten met meeste bomen:")
print(top10.to_string(index=False))

# ── 4. Statische choropleth (PNG) ─────────────────────────────────────────────
print("\nStatische kaart opslaan...")
fig, ax = plt.subplots(1, 1, figsize=(14, 12))
buurten.plot(
    column="aantal_bomen",
    cmap="YlGn",
    legend=True,
    legend_kwds={"label": "Aantal bomen", "shrink": 0.6},
    edgecolor="#666666",
    linewidth=0.4,
    ax=ax,
    missing_kwds={"color": "#eeeeee", "label": "Geen data"},
)
# Voeg buurtnamen toe voor top 10
for _, row in buurten.nlargest(10, "aantal_bomen").iterrows():
    cx = row.geometry.centroid.x
    cy = row.geometry.centroid.y
    ax.annotate(
        f"{row['BUURTNAAM']}\n{row['aantal_bomen']:,}",
        xy=(cx, cy), ha="center", va="center",
        fontsize=5.5, color="#222222",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.6, ec="none"),
    )
ax.set_title("Bomen per buurt – Gemeente Rotterdam", fontsize=16, pad=12)
ax.set_axis_off()
plt.tight_layout()
out_png = OUT / "bomen_per_buurt.png"
plt.savefig(out_png, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Opgeslagen: {out_png}")

# ── 5. Interactieve Folium choropleth (HTML) ──────────────────────────────────
print("Interactieve kaart opslaan...")
buurten_wgs = buurten.to_crs(epsg=4326)

m = folium.Map(location=[51.9225, 4.47917], zoom_start=12, tiles="CartoDB positron")

choropleth = folium.Choropleth(
    geo_data=buurten_wgs.__geo_interface__,
    data=buurten_wgs,
    columns=["BUURTNAAM", "aantal_bomen"],
    key_on="feature.properties.BUURTNAAM",
    fill_color="YlGn",
    fill_opacity=0.75,
    line_opacity=0.5,
    nan_fill_color="#eeeeee",
    legend_name="Aantal bomen per buurt",
    highlight=True,
).add_to(m)

# Tooltip met naam + aantal
folium.GeoJsonTooltip(
    fields=["BUURTNAAM", "GEBDNAAM", "aantal_bomen"],
    aliases=["Buurt:", "Gebied:", "Aantal bomen:"],
    style="font-size:13px;",
).add_to(choropleth.geojson)

folium.LayerControl().add_to(m)

out_html = OUT / "bomen_per_buurt.html"
m.save(str(out_html))
print(f"  Opgeslagen: {out_html}")

print("\nKlaar!")
