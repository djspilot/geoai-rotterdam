"""Aantal bomen per subbuurt in Rotterdam — proportionele cirkels.

Per TIR-subbuurt het **absolute** aantal bomen, als cirkel op de centroïde. Bewust
géén choropleet: de gebruikersvraag ging over aantallen, niet over dichtheid. Bij
proportionele symbolen draagt de cirkel*oppervlakte* de waarde (niet het vlak), dus
de normalisatie-eis van invariant 3 geldt hier niet — absolute aantallen zijn correct.

- `s` (oppervlak in pt²) **lineair** in het aantal, zodat de straal ∝ √aantal;
- `S_MAX = 170`: afgestemd op 578 subbuurten — groter en de cirkels lopen in het
  centrum in elkaar over (op buurtniveau, 91 vlakken, werkt ~620);
- subbuurten **zonder bomen** krijgen een lichtgrijze vulling en een eigen
  legenda-item: nul is een waarde, geen afwezigheid. Zonder die klasse is "geen
  cirkel" niet te onderscheiden van "buiten de data";
- legenda via `add_proportional_legend(..., extras=...)`, ná `finalize_map` +
  `fit_figure_to_data` (invariant 8);
- key = `TEKST` (TIR-code): buurt-/subbuurtnamen zijn niet uniek.

Bron: Obsurv via diensten.rotterdam.nl.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt

from rotterdam import (
    ASSET_COLORS, STYLE, add_proportional_legend, add_rotterdam_basemap,
    count_per_polygon, finalize_map, fit_figure_to_data, load_layer, safe_centroids,
    save_map, setup_headless_matplotlib, style_map, validate_map,
)

setup_headless_matplotlib()

S_MAX = 170                 # grootste cirkel (scatter s, pt²) — zie docstring
GEEN_BOMEN = "#c4c4c4"      # vulling voor subbuurten met 0 bomen
GEEN_ALPHA = 0.5            # laag genoeg om de basemap eronder leesbaar te houden

subbuurten = load_layer("subbuurten")
bomen = load_layer("bomen")

per_sb = count_per_polygon(bomen, subbuurten, key="TEKST")
per_sb["n"] = per_sb["n"].astype(int)
nmax = per_sb["n"].max()
leeg = per_sb[per_sb["n"] == 0]
print(f"{len(subbuurten)} subbuurten, {len(bomen)} bomen | max {nmax} | "
      f"mediaan {per_sb['n'].median():.0f} | zonder bomen: {len(leeg)}")

pts, sizes = [], []
for row, c in safe_centroids(per_sb):
    if row["n"] <= 0:                       # 0 => geen cirkel maar de grijze klasse
        continue
    pts.append((c.x, c.y))
    sizes.append(row["n"] / nmax * S_MAX)

fig, ax = plt.subplots(figsize=(12, 10))
per_sb.plot(ax=ax, facecolor="none", edgecolor=STYLE["boundary_color"],
            linewidth=0.25, zorder=2)
leeg.plot(ax=ax, facecolor=GEEN_BOMEN, edgecolor=STYLE["boundary_color"],
          linewidth=0.25, alpha=GEEN_ALPHA, zorder=2.5)
add_rotterdam_basemap(ax, layer="kleur")
ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=sizes,
           facecolor=ASSET_COLORS["bomen"], edgecolor="#14512c",
           linewidth=0.4, alpha=0.65, zorder=3)

style_map(ax, "Aantal bomen per subbuurt — Rotterdam",
          subtitle="cirkeloppervlak evenredig aan het aantal bomen (Obsurv)")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

legend_vals = [200, 1000, int(round(nmax / 100) * 100)]
add_proportional_legend(
    ax, legend_vals, [v / nmax * S_MAX for v in legend_vals],
    title="Aantal bomen", corner="auto",
    facecolor=ASSET_COLORS["bomen"], edgecolor="#14512c", alpha=0.65,
    extras=[(GEEN_BOMEN, "Geen bomen")], extra_alpha=GEEN_ALPHA,
)

for w in validate_map(fig, ax, data=per_sb):
    print("WARN:", w)

print(save_map(fig, "bomen_per_subbuurt_proportioneel"))
