"""Aantal afvalbakken per subbuurt in Rotterdam — proportionele symbolen.

Gemaakt met de rotterdam-geoai skill. Een *aantal* per gebied hoort niet als
ruwe-count-choropleet (invariant 3: dat is misleidend, grote subbuurten krijgen
vanzelf meer), maar als proportioneel symbool: cirkeloppervlak evenredig aan het
aantal afvalbakken per subbuurt.
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import matplotlib.pyplot as plt

from rotterdam import (
    load_layer, style_map, finalize_map, fit_figure_to_data,
    add_proportional_legend, validate_map, save_map,
    setup_headless_matplotlib, RD_NEW, ASSET_COLORS,
)

setup_headless_matplotlib()
KLEUR = ASSET_COLORS["afvalbak"]
SCHAAL = 6.0                      # cirkeloppervlak (points^2) per afvalbak

# 1. Data + telling per subbuurt
sub = load_layer("subbuurten")
gemeente = load_layer("gemeente")
afval = load_layer("afvalbak")
j = gpd.sjoin(afval[["geometry"]], sub, how="inner", predicate="within")
sub["n_afval"] = sub.index.map(j.groupby(j.index_right).size()).fillna(0).astype(int)
pts = sub[sub["n_afval"] > 0].copy()
pts["pt"] = pts.geometry.representative_point()
print(f"{sub['n_afval'].sum()} afvalbakken over {(sub['n_afval']>0).sum()} subbuurten "
      f"(max {sub['n_afval'].max()} per subbuurt)")

# 2. Tekenen — subbuurtgrenzen als lichte context + proportionele cirkels
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_aspect("equal")
sub.boundary.plot(ax=ax, color="#d8d8d8", linewidth=0.2, zorder=2)
gemeente.boundary.plot(ax=ax, color="#333333", linewidth=1.0, zorder=3)
ax.scatter(pts["pt"].x, pts["pt"].y, s=pts["n_afval"] * SCHAAL,
           facecolor=KLEUR, edgecolor="white", linewidth=0.3, alpha=0.6, zorder=5)

# 3. Kaartelementen + footer. Geen basemap: 494 cirkels + 578 subbuurtgrenzen op een
#    kleur-basemap worden onleesbaar (afwijking van invariant 10, hier bewust).
style_map(ax, "Afvalbakken per subbuurt — Rotterdam",
          subtitle="aantal afvalbakken per subbuurt (Obsurv)")
finalize_map(fig, source="Obsurv (afvalbakken) + TIR-subbuurten via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

# 4. Proportionele-symbool legenda (invariant 9), datavrije hoek (invariant 8)
legend_vals = [10, 50, 100]
add_proportional_legend(
    ax, values=legend_vals, sizes=[v * SCHAAL for v in legend_vals],
    title="Afvalbakken", corner="auto", facecolor=KLEUR, edgecolor="white",
    data=gpd.GeoSeries(list(pts["pt"].values), crs=RD_NEW),
)

warns = validate_map(fig, ax, data=sub, normalized=True)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")
out = save_map(fig, "afvalbakken_per_subbuurt")
print("Kaart opgeslagen:", out)
