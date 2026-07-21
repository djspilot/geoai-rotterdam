"""Aantal bomen per buurt in Rotterdam — proportionele cirkels.

Buurt-versie van `kaart_bomen_per_subbuurt_proportioneel.py`; zelfde methode, ander
detailniveau. Per TIR-buurt het **absolute** aantal bomen als cirkel op de centroïde.
Bewust géén choropleet: de vraag ging over aantallen, niet over dichtheid. Bij
proportionele symbolen draagt de cirkel*oppervlakte* de waarde (niet het vlak), dus
de normalisatie-eis van invariant 3 geldt hier niet.

- `s` (oppervlak in pt²) **lineair** in het aantal, zodat de straal ∝ √aantal;
- `S_MAX = 620`: afgestemd op 91 buurten. Op subbuurtniveau (578 vlakken) moet dit
  naar ~170, anders lopen de cirkels in het centrum in elkaar over;
- buurten **zonder bomen** krijgen een lichtgrijze vulling en een eigen legenda-item:
  nul is een waarde, geen afwezigheid;
- legenda via `add_proportional_legend(..., extras=...)`, ná `finalize_map` +
  `fit_figure_to_data` (invariant 8);
- key = `TEKST` (TIR-code): buurtnamen zijn niet uniek (bv. "Dorp").

Op dit niveau valt het centrum samen tot één kluwen cirkels; voor de fijnere
structuur is de subbuurt-versie leesbaarder.

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

S_MAX = 620                 # grootste cirkel (scatter s, pt²) — zie docstring
GEEN_BOMEN = "#c4c4c4"      # vulling voor buurten met 0 bomen
GEEN_ALPHA = 0.5            # laag genoeg om de basemap eronder leesbaar te houden

buurten = load_layer("buurten")
bomen = load_layer("bomen")

per_buurt = count_per_polygon(bomen, buurten, key="TEKST")
per_buurt["n"] = per_buurt["n"].astype(int)
nmax = per_buurt["n"].max()
leeg = per_buurt[per_buurt["n"] == 0]
print(f"{len(buurten)} buurten, {len(bomen)} bomen | max {nmax} | "
      f"mediaan {per_buurt['n'].median():.0f} | zonder bomen: {len(leeg)}")
print(per_buurt.nlargest(5, "n")[["TEKST", "BUURTNAAM", "n"]].to_string(index=False))

pts, sizes = [], []
for row, c in safe_centroids(per_buurt):
    if row["n"] <= 0:                       # 0 => geen cirkel maar de grijze klasse
        continue
    pts.append((c.x, c.y))
    sizes.append(row["n"] / nmax * S_MAX)

fig, ax = plt.subplots(figsize=(12, 10))
per_buurt.plot(ax=ax, facecolor="none", edgecolor=STYLE["boundary_color"],
               linewidth=STYLE["boundary_width"], zorder=2)
leeg.plot(ax=ax, facecolor=GEEN_BOMEN, edgecolor=STYLE["boundary_color"],
          linewidth=STYLE["boundary_width"], alpha=GEEN_ALPHA, zorder=2.5)
add_rotterdam_basemap(ax, layer="kleur")
ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=sizes,
           facecolor=ASSET_COLORS["bomen"], edgecolor="#14512c",
           linewidth=0.6, alpha=0.65, zorder=3)

style_map(ax, "Aantal bomen per buurt — Rotterdam",
          subtitle="cirkeloppervlak evenredig aan het aantal bomen (Obsurv)")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

legend_vals = [500, 2000, int(round(nmax / 500) * 500)]
add_proportional_legend(
    ax, legend_vals, [v / nmax * S_MAX for v in legend_vals],
    title="Aantal bomen", corner="auto",
    facecolor=ASSET_COLORS["bomen"], edgecolor="#14512c", alpha=0.65,
    extras=[(GEEN_BOMEN, "Geen bomen")], extra_alpha=GEEN_ALPHA,
)

for w in validate_map(fig, ax, data=per_buurt):
    print("WARN:", w)

print(save_map(fig, "bomen_per_buurt_proportioneel"))
