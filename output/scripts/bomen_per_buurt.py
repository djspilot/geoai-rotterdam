"""Bomen per buurt - choropleth kaart (statisch + interactief)."""

import glob
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "General data"))
from rotterdam import choropleth, finalize_map, save_map, validate_map

BASE = ROOT / "General data" / "Data"
OUT  = ROOT / "output" / "maps"

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

# Normaliseren (invariant 3): bomen per hectare i.p.v. ruwe aantallen
buurten["opp_ha"] = buurten.geometry.area / 10_000.0
buurten["bomen_per_ha"] = (buurten["aantal_bomen"] / buurten["opp_ha"]).round(1)

top10 = buurten.nlargest(10, "aantal_bomen")[["BUURTNAAM", "GEBDNAAM", "aantal_bomen"]]
print("\nTop 10 buurten met meeste bomen:")
print(top10.to_string(index=False))

# ── 4. Statische choropleet (genormaliseerd: bomen per hectare) ──────────────
print("\nStatische kaart opslaan...")
fig, ax = choropleth(
    buurten, "bomen_per_ha", cmap="YlGn",
    title="Boomdichtheid per buurt — Gemeente Rotterdam",
    subtitle="bomen per hectare (Obsurv)",
)
# top-5 dichtste buurten labelen
for _, row in buurten.nlargest(5, "bomen_per_ha").iterrows():
    c = row.geometry.representative_point()
    ax.annotate(
        str(row["BUURTNAAM"]), xy=(c.x, c.y), ha="center", va="center",
        fontsize=6, color="#222222",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.6, ec="none"),
    )
finalize_map(fig, source="Obsurv (bomen) + TIR-buurten via diensten.rotterdam.nl")
warns = validate_map(fig, ax, data=buurten, normalized=True)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out_png = save_map(fig, "bomen_per_buurt")
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
