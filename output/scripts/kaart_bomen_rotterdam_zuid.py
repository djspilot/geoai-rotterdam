"""Statische kaart: alle bomen in Rotterdam Zuid."""

import glob
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# --- Helper ---
def load_rd(path):
    """Load GeoJSON ensuring EPSG:28992. Some Rotterdam files have wrong CRS metadata."""
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=28992)
    else:
        # Check if coordinates are already in RD New range despite wrong CRS label
        bounds = gdf.total_bounds
        if bounds[0] > 10000 and bounds[1] > 300000:
            # Coordinates are RD New, override wrong CRS
            gdf = gdf.set_crs(epsg=28992, allow_override=True)
        elif gdf.crs.to_epsg() != 28992:
            gdf = gdf.to_crs(epsg=28992)
    return gdf

# --- TIR gebieden laden ---
gebieden = load_rd("General data/Data/tir_gebieden.geojson")

# Rotterdam Zuid: gebieden ten zuiden van de Maas
zuid_namen = [
    "Feijenoord",
    "IJsselmonde",
    "Charlois",
    "Hoogvliet",
    "Pernis",
    "Rozenburg",
    "Waalhaven-Eemhaven",
    "Vondelingenplaat",
]
zuid = gebieden[gebieden["GEBDNAAM"].isin(zuid_namen)]
# Repareer geometrie
zuid = zuid.copy()
zuid["geometry"] = zuid["geometry"].make_valid()

# --- Bomen laden (chunks) ---
print("Bomen laden...")
chunks = sorted(glob.glob("General data/Data/bomen_chunks/*.geojson"))
bomen = pd.concat([gpd.read_file(c) for c in chunks], ignore_index=True)
bomen = gpd.GeoDataFrame(bomen, geometry="geometry", crs="EPSG:28992")
print(f"  Totaal: {len(bomen)} bomen")

# --- Filter: spatial join met Rotterdam Zuid gebieden ---
print("Filteren op Rotterdam Zuid...")
bomen_zuid = gpd.sjoin(bomen, zuid[["geometry", "GEBDNAAM"]], how="inner", predicate="within")
print(f"  Bomen in Rotterdam Zuid: {len(bomen_zuid)}")

# --- Kaart maken ---
fig, ax = plt.subplots(1, 1, figsize=(16, 12))

# Achtergrond: gebiedsgrenzen
zuid.plot(ax=ax, color="#f0f0f0", edgecolor="#999999", linewidth=1.0)

# Bomen als kleine punten
bomen_zuid.plot(
    ax=ax,
    color="#2d8a4e",
    markersize=0.3,
    alpha=0.5,
)

# Labels per gebied
for _, row in zuid.iterrows():
    if row.geometry is None or row.geometry.is_empty:
        continue
    centroid = row.geometry.centroid
    if centroid.is_empty:
        continue
    ax.annotate(
        row["GEBDNAAM"],
        xy=(centroid.x, centroid.y),
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="#333333",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7, edgecolor="none"),
    )

ax.set_title(
    f"Alle bomen in Rotterdam Zuid ({len(bomen_zuid):,} bomen)",
    fontsize=16,
    fontweight="bold",
    pad=15,
)
ax.set_axis_off()
plt.tight_layout()

out = "output/kaart_bomen_rotterdam_zuid.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Kaart opgeslagen: {out}")
plt.close()
