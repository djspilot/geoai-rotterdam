"""Inwonertal per buurt in Rotterdam als proportionele cirkels.

Elke CBS-buurt krijgt een cirkel op zijn representatieve punt; het *oppervlak*
van de cirkel is evenredig met het inwonertal (straal ~ sqrt(inwoners)), zodat
grote en kleine buurten eerlijk vergelijkbaar zijn. Grootste cirkels achterin
(zorg dat kleine niet verdwijnen), lichte transparantie tegen overlap.

- data: CBS Wijk- en Buurtkaart 2024 via `cbs_buurten_rotterdam()` (87 buurten,
  ~670.585 inwoners; havengebied is leeg en toont dus geen cirkels),
- grootte-legenda met ronde referentiewaarden die het bereik dekken,
- de legenda staat via `place_legend(corner="auto")` op een datavrije plek en
  overlapt nooit de cirkels, noordpijl of schaalstok (harde invariant 8),
- grijze Rotterdamse basemap (met PDOK-fallback).

Bron: CBS Wijk- en Buurtkaart 2024 (PDOK WFS).
"""

import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import numpy as np
import matplotlib.pyplot as plt

from rotterdam import (
    load_layer, cbs_buurten_rotterdam, style_map, add_scalebar,
    add_rotterdam_basemap, add_pdok_basemap, finalize_map, fit_figure_to_data,
    add_proportional_legend, save_map, setup_headless_matplotlib,
)

setup_headless_matplotlib()
CIRKEL, RAND = "#2c7fb8", "#0b3d5c"

buurten = cbs_buurten_rotterdam(2024)
print(f"buurten met inwoners: {len(buurten)}  | "
      f"totaal inwoners: {int(buurten['aantal_inwoners'].sum()):,}")

pop = buurten["aantal_inwoners"].to_numpy()
pmax = int(pop.max())
print("grootste buurt:", pmax, "inwoners")

# oppervlak (scatter 's') ~ inwonertal  => straal ~ sqrt(inwoners)
S_MAX = 1600.0
scale = S_MAX / pmax
cent = buurten.geometry.representative_point()
xs, ys = cent.x.to_numpy(), cent.y.to_numpy()
sizes = pop * scale
order = np.argsort(-pop)   # grootste eerst -> achterin

gemeente = load_layer("gemeente")

fig, ax = plt.subplots(figsize=(13, 11))
gemeente.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=4)
# buurtgrenzen: dunne zwarte lijn zodat de lezer ziet waar elke buurt ligt
# (zwart voor contrast met de basemap; onder de cirkels)
buurten.boundary.plot(ax=ax, color="#000000", linewidth=0.4, alpha=0.7, zorder=5)
ax.scatter(xs[order], ys[order], s=sizes[order], facecolor=CIRKEL, edgecolor=RAND,
           linewidths=0.5, alpha=0.55, zorder=6)

# grijze basemap (esthetische keuze): neutrale onderlaag houdt de cirkels op de
# voorgrond. Invariant 12: eigen Rotterdam-basemap niet vermelden, derde-partij wel.
bron_delen = ["CBS Wijk- en Buurtkaart 2024"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as e:
    print("fallback PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "Inwonertal per buurt in Rotterdam")
add_scalebar(ax, inside=True)
finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# grootte-legenda ná fit_figure_to_data (definitieve figuurhoogte -> correcte
# auto-plaatsing); corner="auto" mijdt automatisch alle lagen
refs = [2500, 10000, 25000]
refs = [r for r in refs if r <= pmax] or [pmax]
add_proportional_legend(ax, values=refs, sizes=[r * scale for r in refs],
                        title="Inwoners", corner="auto",
                        facecolor=CIRKEL, edgecolor=RAND, alpha=0.55)

print("opgeslagen:", save_map(fig, "inwonertal_per_buurt_rotterdam"))
