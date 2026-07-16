"""Oriëntatiekaart Rotterdam Centrum — demo van Noordpijl B + Schaalstok B.

Buurtgrenzen (contour) + afvalbakken als punten. Oriëntatie/afstand zijn hier
relevant, dus een noordpijl (variant B, volledig zwart) en een schaalstok
(variant B, enkele lijn met streepjes) horen erbij.
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, filter_to_area, style_map, add_scalebar, finalize_map,
    place_legend, add_rotterdam_basemap, add_pdok_basemap,
    setup_headless_matplotlib, ASSET_COLORS, MAPS_DIR,
)

setup_headless_matplotlib()

GEBIED = "Rotterdam Centrum"

# 1. Data (lokaal)
gebieden = load_layer("gebieden")
buurten = load_layer("buurten")
afval = load_layer("afvalbak")

centrum = gebieden[gebieden["GEBDNAAM"] == GEBIED]
centrum_buurten = buurten[buurten["GEBDNAAM"] == GEBIED]
afval_centrum = filter_to_area(afval, gebieden, gebied_names=[GEBIED])
print(f"{len(centrum_buurten)} buurten, {len(afval_centrum)} afvalbakken in {GEBIED}")

# 2. Tekenen (grenzen met witte casing zodat ze op de basemap leesbaar blijven)
import matplotlib.patheffects as pe
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect("equal")
casing = [pe.withStroke(linewidth=2.2, foreground="white")]
centrum_buurten.boundary.plot(ax=ax, color="#333333", linewidth=0.8, zorder=5,
                              path_effects=casing)
centrum.boundary.plot(ax=ax, color="#111111", linewidth=1.8, zorder=6,
                      path_effects=casing)
afval_centrum.plot(ax=ax, color=ASSET_COLORS["afvalbak"], markersize=6,
                   alpha=0.9, zorder=7)

# 3. Gekleurde Rotterdamse basemap (invariant 10), met PDOK-fallback. De eigen
#    basemap hoeft niet in de bron; de PDOK-fallback (derde partij) wél (inv. 12).
bron = "TIR + Obsurv via diensten.rotterdam.nl"
try:
    add_rotterdam_basemap(ax, layer="kleur")
except Exception as e:
    print("Rotterdam-basemap faalde, val terug op PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="standaard")
    bron += " · Basiskaart: PDOK BRT"

# 4. Kaartelementen: titel + subtitel (boven de kaart), noordpijl B, schaalstok B
style_map(ax, "Rotterdam Centrum — oriëntatiekaart",
          subtitle="Buurten en afvalbakken · Noordpijl B + Schaalstok B",
          north=True, north_variant="B")
add_scalebar(ax, inside=True, variant="B")

# 5. Footer + legenda (datavrije hoek)
finalize_map(fig, source=bron)
handles = [
    Line2D([0], [0], marker="o", linestyle="none", markersize=6,
           markerfacecolor=ASSET_COLORS["afvalbak"], markeredgecolor="none",
           label="Afvalbak"),
    Line2D([0], [0], color="#888888", linewidth=0.9, label="Buurtgrens"),
    Line2D([0], [0], color="#1a1a1a", linewidth=1.4, label="Gebiedsgrens"),
]
place_legend(ax, handles, [h.get_label() for h in handles],
             corner="auto", data=afval_centrum)

out = MAPS_DIR / "rotterdam_centrum_orientatie.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print("opgeslagen:", out)
