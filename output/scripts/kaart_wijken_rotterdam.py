"""Overzichtskaart van alle wijken van Rotterdam.

Toont de wijkgrenzen in zwart zonder vlakvulling, met per wijk het wijknummer op
de kaart en een genummerde naamlijst in een zijpaneel (nummer -> naam). Met 91
wijken zou nummer + naam direct op elke wijk onleesbaar overlappen; de lijst
koppelt beide.

Wijk = TIR-buurt (invariant 2: WIJK = TIR-buurt). Uit `load_layer("buurten")`:
`BUURTNAAM` = wijknaam, `BUURT` = wijknummer. Namen komen overeen met de
officiële Rotterdamse wijken (Stadsdriehoek, Cool, Oude Westen, ...).

Bron: Gebiedsindeling Gemeente Rotterdam (TIR).
"""

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

from rotterdam import (
    load_layer, style_map, add_scalebar, add_rotterdam_basemap, add_pdok_basemap,
    finalize_map, fit_figure_to_data, add_side_panel, save_map,
    setup_headless_matplotlib, RD_NEW,
)

setup_headless_matplotlib()

wijken = (load_layer("buurten").to_crs(RD_NEW)
          .sort_values("BUURT").reset_index(drop=True))
print("wijken:", len(wijken))

fig, ax = plt.subplots(figsize=(13, 11))
wijken.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.9, zorder=6)

# wijknummer op een representatief punt binnen elke wijk, met witte halo
halo = [pe.withStroke(linewidth=2.0, foreground="white")]
for _, r in wijken.iterrows():
    p = r.geometry.representative_point()
    ax.text(p.x, p.y, str(int(r["BUURT"])), fontsize=7, ha="center", va="center",
            color="black", fontweight="bold", zorder=7, path_effects=halo,
            clip_on=True)

# grijze basemap (neutrale onderlaag onder de labels). Invariant 12: eigen
# Rotterdam-basemap niet vermelden, PDOK-fallback (derde partij) wél.
bron_delen = ["Gebiedsindeling: Gemeente Rotterdam (TIR)"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as e:
    print("fallback PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "Wijken in Rotterdam")
add_scalebar(ax, inside=True)

finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# zijpaneel: genummerde naamlijst in 2 kolommen (nummer -> naam)
panel = add_side_panel(fig, ax, width_in=4.4, gap_in=0.15)
panel.text(0.0, 1.0, "Wijken", fontweight="bold", fontsize=11, va="top", ha="left")
rows = wijken[["BUURT", "BUURTNAAM"]].values.tolist()
ncol = 2
per = math.ceil(len(rows) / ncol)
top, bottom = 0.955, 0.005
lh = (top - bottom) / per
colw = 1.0 / ncol
for i, (nr, naam) in enumerate(rows):
    col, row = divmod(i, per)
    x0 = col * colw
    y = top - row * lh
    panel.text(x0 + 0.07, y, f"{int(nr)}", fontsize=7, ha="right", va="top",
               fontweight="bold", color="#222222")
    panel.text(x0 + 0.09, y, str(naam), fontsize=7, ha="left", va="top",
               color="#222222")

print("opgeslagen:", save_map(fig, "wijken_rotterdam"))
