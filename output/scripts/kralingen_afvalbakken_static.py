"""Statische kaart: Kralingen-Crooswijk met afvalbakken per buurt."""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "General data" / "Data"
OUT  = ROOT / "output" / "maps"

# ── Data laden ────────────────────────────────────────────────────────────────
buurten = gpd.read_file(BASE / "tir_buurten.geojson").set_crs(epsg=28992, allow_override=True)
kralingen = buurten[buurten["GEBDNAAM"] == "Kralingen-Crooswijk"].copy()

afval = gpd.read_file(BASE / "afvalbak.geojson").set_crs(epsg=28992, allow_override=True)
afval_kralingen = gpd.sjoin(afval, kralingen[["BUURTNAAM", "geometry"]], how="inner", predicate="within")

# ── Kleuren per buurt ─────────────────────────────────────────────────────────
KLEUREN = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12",
           "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]
buurt_namen = sorted(kralingen["BUURTNAAM"].unique())
kleur_map = {naam: KLEUREN[i % len(KLEUREN)] for i, naam in enumerate(buurt_namen)}
kralingen["kleur"] = kralingen["BUURTNAAM"].map(kleur_map)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 11))

# Buurt polygonen
for _, row in kralingen.iterrows():
    gpd.GeoDataFrame([row], crs=kralingen.crs).plot(
        ax=ax, color=row["kleur"], edgecolor="#333333",
        linewidth=1.5, alpha=0.25,
    )

# Afvalbakken
for buurt_naam in buurt_namen:
    subset = afval_kralingen[afval_kralingen["BUURTNAAM"] == buurt_naam]
    ax.scatter(
        subset.geometry.x, subset.geometry.y,
        color=kleur_map[buurt_naam], s=8, alpha=0.75,
        zorder=3, label=buurt_naam,
    )

# Buurtgrenzen opnieuw bovenop voor duidelijkheid
kralingen.boundary.plot(ax=ax, color="#333333", linewidth=1.5, zorder=4)

# Buurtnamen als labels
for _, row in kralingen.iterrows():
    cx = row.geometry.centroid.x
    cy = row.geometry.centroid.y
    n = len(afval_kralingen[afval_kralingen["BUURTNAAM"] == row["BUURTNAAM"]])
    ax.annotate(
        f"{row['BUURTNAAM']}\n({n})",
        xy=(cx, cy), ha="center", va="center",
        fontsize=8, fontweight="bold", color="#222222",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7, ec="none"),
        zorder=5,
    )

# Legenda
patches = [
    mpatches.Patch(color=kleur_map[naam], label=f"{naam}  ({len(afval_kralingen[afval_kralingen['BUURTNAAM']==naam])})")
    for naam in buurt_namen
]
ax.legend(handles=patches, title="Buurt (aantal afvalbakken)",
          loc="lower right", fontsize=8, title_fontsize=9,
          framealpha=0.9, edgecolor="#cccccc")

totaal = len(afval_kralingen)
ax.set_title(f"Afvalbakken in Kralingen-Crooswijk  (totaal: {totaal})",
             fontsize=14, fontweight="bold", pad=14)
ax.set_axis_off()
plt.tight_layout()

out = OUT / "kralingen_afvalbakken.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Opgeslagen: {out}")
