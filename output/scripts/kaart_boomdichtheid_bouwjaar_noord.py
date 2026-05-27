"""Boomdichtheid vs bouwjaarklasse — Rotterdam Noord.

Twee-paneel choropleet per CBS-buurt + scatter-inset:
- Links:  bomen per hectare landoppervlak (n_bomen / oppervlakteLandInHa)
- Rechts: % woningen bouwjaarklasse < 2000 (CBS 2023). Hoger = ouder.
- Inset:  scatter %oud vs bomen/ha, Pearson r.

Hypothese: vooroorlogse lanen-wijken hebben meer volwassen bomen dan
recent ontwikkelde gebieden. Positieve r bevestigt dat.
"""

from __future__ import annotations

import glob
import sys
from urllib.parse import urlencode

sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rotterdam import (
    DATA_OUT,
    LOCAL_FILES,
    RD_NEW,
    ROTTERDAM_NOORD_GEBIEDEN,
    finalize_map,
    load_layer,
    load_rotterdam,
    save_map,
    style_map,
    validate_map,
)
from rotterdam.cartography import setup_headless_matplotlib

setup_headless_matplotlib()

OLD_COL = "percentageBouwjaarklasseTot2000"
LAND_HA_COL = "oppervlakteLandInHa"
CBS_YEAR = 2023

# 1. Noord polygon (TIR)
gebieden = load_layer("gebieden")
noord = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_NOORD_GEBIEDEN)].copy()
noord_union = noord.dissolve().geometry.iloc[0]
xmin, ymin, xmax, ymax = noord.total_bounds

# 2. CBS-buurten Rotterdam binnen Noord-bbox (CQL_FILTER wordt genegeerd)
pad = 2000
cbs_url = f"https://service.pdok.nl/cbs/wijkenbuurten/{CBS_YEAR}/wfs/v1_0?" + urlencode({
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "typeNames": "wijkenbuurten:buurten", "outputFormat": "application/json",
    "count": "5000",
    "bbox": f"{xmin-pad},{ymin-pad},{xmax+pad},{ymax+pad},EPSG:28992",
})
cbs = gpd.read_file(cbs_url).to_crs(RD_NEW)
cbs = cbs[cbs["gemeentenaam"] == "Rotterdam"].copy()
cbs[OLD_COL] = pd.to_numeric(cbs[OLD_COL], errors="coerce")
cbs[LAND_HA_COL] = pd.to_numeric(cbs[LAND_HA_COL], errors="coerce")
cbs = cbs[(cbs[OLD_COL] >= 0) & (cbs[OLD_COL] <= 100)
          & (cbs[LAND_HA_COL] > 0)].copy()
cbs_noord = cbs[cbs.geometry.centroid.within(noord_union)].copy()
print(f"CBS-buurten in Noord met bouwjaardata: {len(cbs_noord)}")

# 3. Bomen — alle chunks, clip op Noord-bbox per chunk
chunk_paths = sorted(glob.glob(LOCAL_FILES["bomen_chunks_glob"]))
print(f"Bomen-chunks: {len(chunk_paths)}")
clipped = []
for i, p in enumerate(chunk_paths):
    g = load_rotterdam(p)
    g = g.cx[xmin:xmax, ymin:ymax]
    if len(g):
        clipped.append(g[["geometry"]])
bomen = pd.concat(clipped, ignore_index=True)
bomen = gpd.GeoDataFrame(bomen, geometry="geometry", crs=RD_NEW)
bomen = bomen[bomen.geometry.within(noord_union)].copy()
print(f"Bomen in Noord: {len(bomen):,}")

# 4. Spatial join → bomen per CBS-buurt
joined = gpd.sjoin(bomen, cbs_noord[["buurtcode", "geometry"]],
                   how="inner", predicate="within")
counts = joined.groupby("buurtcode").size().rename("n_bomen")
cbs_noord = cbs_noord.merge(counts, left_on="buurtcode", right_index=True, how="left")
cbs_noord["n_bomen"] = cbs_noord["n_bomen"].fillna(0).astype(int)
cbs_noord["bomen_per_ha"] = cbs_noord["n_bomen"] / cbs_noord[LAND_HA_COL]

# 5. Stats + correlatie
n_buurten = len(cbs_noord)
total_bomen = int(cbs_noord["n_bomen"].sum())
total_ha = float(cbs_noord[LAND_HA_COL].sum())
gem_dichtheid = total_bomen / total_ha
mediaan_oud = cbs_noord[OLD_COL].median()

mask = cbs_noord["bomen_per_ha"].notna() & cbs_noord[OLD_COL].notna()
sub = cbs_noord.loc[mask, ["bomen_per_ha", OLD_COL]]
p99 = sub["bomen_per_ha"].quantile(0.99)
sub_plot = sub[sub["bomen_per_ha"] <= p99]
corr = sub["bomen_per_ha"].corr(sub[OLD_COL])

# 6. Plot
fig, axes = plt.subplots(1, 2, figsize=(16, 9), constrained_layout=False)
noord_border = noord.boundary

# Panel 1: bomen per ha (groen)
ax1 = axes[0]
cbs_noord.plot(
    ax=ax1, column="bomen_per_ha", cmap="Greens",
    scheme="quantiles", k=5, legend=True,
    legend_kwds={"title": "bomen / ha", "loc": "lower left",
                 "fontsize": 8, "title_fontsize": 9, "frameon": True,
                 "fmt": "{:.1f}"},
    edgecolor="white", linewidth=0.3,
)
noord_border.plot(ax=ax1, color="black", linewidth=1.0)
style_map(ax1, "Boomdichtheid",
          subtitle=f"per CBS-buurt, n={n_buurten}")

# Inset scatter
inset = ax1.inset_axes([0.64, 0.66, 0.34, 0.30])
inset.scatter(sub_plot[OLD_COL], sub_plot["bomen_per_ha"],
              s=12, alpha=0.55, color="#2e7d32")
if len(sub_plot) >= 5:
    coef = np.polyfit(sub_plot[OLD_COL], sub_plot["bomen_per_ha"], 1)
    xs = np.linspace(sub_plot[OLD_COL].min(), sub_plot[OLD_COL].max(), 30)
    inset.plot(xs, coef[0]*xs + coef[1], color="#c0392b", linewidth=1.4)
inset.set_xlabel("% woningen < 2000", fontsize=7)
inset.set_ylabel("bomen / ha", fontsize=7)
inset.set_title(f"correlatie r = {corr:+.2f}", fontsize=8)
inset.tick_params(labelsize=6)
inset.set_facecolor("#fafafa")

# Panel 2: % woningen < 2000 (oranje = ouder)
ax2 = axes[1]
cbs_noord.plot(
    ax=ax2, column=OLD_COL, cmap="OrRd",
    scheme="quantiles", k=5, legend=True,
    legend_kwds={"title": "% woningen\nbouwjaar < 2000",
                 "loc": "lower left", "fontsize": 8, "title_fontsize": 9,
                 "frameon": True, "fmt": "{:.0f}"},
    edgecolor="white", linewidth=0.3,
)
noord_border.plot(ax=ax2, color="black", linewidth=1.0)
style_map(ax2, "Bouwjaar-aandeel oud",
          subtitle=f"mediaan {mediaan_oud:.0f}% < 2000")

interpretatie = (
    "r > 0: oudere wijken meer bomen per ha (volwassen lanen).  "
    "r < 0: nieuwere wijken meer bomen."
)

finalize_map(
    fig,
    source=f"Obsurv (bomen) + CBS Wijk- en Buurtkaart {CBS_YEAR} (bouwjaar, oppervlak)",
    date="2026-05-27",
    suptitle="Boomdichtheid vs bouwjaar — Rotterdam Noord",
    suptitle_subtitle=interpretatie,
)
warns = validate_map(fig, axes[0], data=cbs_noord, normalized=True)
for w in warns:
    print("WARN:", w)

out = save_map(fig, "boomdichtheid_bouwjaar_noord")
print(f"map saved -> {out}")

csv_path = DATA_OUT / "boomdichtheid_bouwjaar_noord.csv"
cbs_noord[["buurtcode", "buurtnaam", "n_bomen", LAND_HA_COL,
           "bomen_per_ha", OLD_COL]].sort_values(
    "bomen_per_ha", ascending=False
).to_csv(csv_path, index=False)
print(f"csv saved  -> {csv_path}")

print()
print("=== Topregels ===")
print(f"CBS-buurten in Noord:   {n_buurten}")
print(f"Totaal bomen:           {total_bomen:,}")
print(f"Totaal landoppervlakte: {total_ha:.0f} ha")
print(f"Gem. boomdichtheid:     {gem_dichtheid:.1f} bomen / ha")
print(f"Mediaan % oud:          {mediaan_oud:.1f}%")
print(f"Correlatie (Pearson r): {corr:+.3f}")
