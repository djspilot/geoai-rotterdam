"""Rotterdam op A3 — TIR-grenzen: gemeente, gebied en buurt, alleen contouren.

Gemaakt met de rotterdam-geoai skill. Ongevulde vlakken; lijnhiërarchie:
gemeentegrens (dik, zwart) > gebiedsgrens (middel) > buurtgrens (dun, grijs).
A3 liggend (420 x 297 mm); print-klare PDF (vector) + PNG.
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, style_map, finalize_map, place_legend,
    setup_headless_matplotlib, MAPS_DIR,
)

setup_headless_matplotlib()

# 1. TIR-lagen (drie bovenste niveaus)
gemeente = load_layer("gemeente")
gebieden = load_layer("gebieden")
buurten = load_layer("buurten")
print(f"gemeente={len(gemeente)}  gebieden={len(gebieden)}  buurten={len(buurten)}")

# 2. A3 liggend (420 x 297 mm)
A3_LANDSCAPE = (420 / 25.4, 297 / 25.4)
fig, ax = plt.subplots(figsize=A3_LANDSCAPE)
ax.set_aspect("equal")

# 3. Contouren (geen vulling), van dun/onder naar dik/boven
GEM = dict(color="#1a1a1a", lw=2.2)
GEB = dict(color="#555555", lw=1.2)
BUU = dict(color="#aaaaaa", lw=0.6)
buurten.boundary.plot(ax=ax, **BUU)
gebieden.boundary.plot(ax=ax, **GEB)
gemeente.boundary.plot(ax=ax, **GEM)

# 4. Kaartelementen: titel + noordpijl (linksboven), schaalstok onderin
# geen noordpijl / schaalstok: noord-boven grenzenkaart, geen navigatie en afstand
# is niet relevant voor de interpretatie (invarianten 13 en 14)
style_map(ax, "Rotterdam — gemeente-, gebieds- en buurtgrenzen",
          subtitle="TIR-indeling · alleen contouren")
ax.set_facecolor("white")          # schone witte achtergrond voor print

# 5. Footer (bron + AI-disclaimer + uitgever). GEEN fit_figure_to_data: A3 blijft A3.
finalize_map(fig, source="TIR via diensten.rotterdam.nl")

# 6. Legenda voor de drie lijntypes (datavrije hoek)
handles = [
    Line2D([0], [0], label="Gemeentegrens", **GEM),
    Line2D([0], [0], label="Gebiedsgrens", **GEB),
    Line2D([0], [0], label="Buurtgrens", **BUU),
]
place_legend(ax, handles=handles, labels=[h.get_label() for h in handles],
             title="Legenda", corner="auto")

# 7. Opslaan op ware A3-grootte (geen tight-bijsnijding, anders klopt het formaat niet)
pdf = MAPS_DIR / "rotterdam_tir_grenzen_a3.pdf"
png = MAPS_DIR / "rotterdam_tir_grenzen_a3.png"
fig.savefig(pdf, facecolor="white")                 # vector, print-klaar
fig.savefig(png, dpi=200, facecolor="white")        # raster-preview
print("opgeslagen:", pdf)
print("opgeslagen:", png)
