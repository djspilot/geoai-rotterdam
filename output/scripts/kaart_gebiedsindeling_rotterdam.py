"""Gebiedsindeling van Rotterdam — de 21 gebieden met hun namen.

Referentiekaart: de indeling zélf is het onderwerp, niet een thema dat erover
verdeeld wordt. Daarom geen thematische kleuring — één neutrale vulling voor alle
gebieden, en de informatie zit in de grenzen en de namen.

Gemaakt voor **bewoners/publiek**, wat de opmaak stuurt:
- namen direct op de kaart in plaats van in een legenda met codes;
- witte halo achter elk label, zodat het leesbaar blijft op de gekleurde basemap;
- mensentaal in titel en subtitel, geen "TIR" of veldnamen.

De gebieden verschillen enorm in oppervlak (Rivium 0,1 km² tegen
Botlek-Europoort-Maasvlakte 136 km²) en liggen in het oosten dicht op elkaar, dus
labels op de centroïde botsen. Een klein iteratief algoritme duwt overlappende
labels verticaal uit elkaar (alleen verticaal: horizontaal schuiven haalt een label
sneller van zijn gebied af) en geeft elk label dat daarbij meer dan 5 punten is
opgeschoven een verwijslijntje naar zijn eigen gebied. In de praktijk zijn dat er 5.

De gebiedsgrenzen zijn donkerder en dikker dan de STYLE-default: op een gekleurde
basemap vallen ze anders weg tegen de wegen, en hier is de grens het onderwerp.

Bron: TIR-gebieden via diensten.rotterdam.nl.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt

from rotterdam import (
    add_rotterdam_basemap, add_swatch_legend, finalize_map, fit_figure_to_data,
    load_layer, save_map, setup_headless_matplotlib, style_map, validate_map,
)

setup_headless_matplotlib()

VULLING = "#f6f3ee"          # neutrale vlakvulling (STYLE-default voor polygonen)
VUL_ALPHA = 0.45             # laag genoeg om de basemap eronder te laten meespreken
GRENS = "#333333"            # donkerder dan STYLE-default: de grens ís het onderwerp
LABEL_FS = 8.5               # groter dan de skill-default: publiekskaart

gebieden = load_layer("gebieden")
gebieden["opp_km2"] = gebieden.geometry.area / 1e6
print(f"{len(gebieden)} gebieden | kleinste {gebieden['opp_km2'].min():.1f} km²"
      f" | grootste {gebieden['opp_km2'].max():.1f} km²")

fig, ax = plt.subplots(figsize=(14, 10))
gebieden.plot(ax=ax, facecolor=VULLING, alpha=VUL_ALPHA,
              edgecolor=GRENS, linewidth=1.6, zorder=2)
add_rotterdam_basemap(ax, layer="kleur")

anchors = [(str(r["GEBDNAAM"]), r.geometry.representative_point())
           for _, r in gebieden.iterrows()]

HALO = [pe.withStroke(linewidth=2.6, foreground="white")]


def _label(text, p, dx, dy, leader):
    """Eén gebiedslabel; met verwijslijntje zodra het van zijn punt is weggeschoven."""
    kw = dict(xy=(p.x, p.y), xytext=(dx, dy), textcoords="offset points",
              ha="center", va="center", fontsize=LABEL_FS, color="#1a1a1a",
              zorder=5, path_effects=HALO)
    if leader:
        kw["arrowprops"] = dict(arrowstyle="-", color="#555555", linewidth=0.6,
                                shrinkA=1, shrinkB=2)
    return ax.annotate(text, **kw)


# Labels op hun punt zetten en dan uit elkaar duwen tot niets meer overlapt.
# Alleen verticaal: horizontaal schuiven haalt een label sneller van zijn gebied af.
offsets = [[0.0, 0.0] for _ in anchors]
artists = [_label(t, p, 0, 0, False) for t, p in anchors]
fig.canvas.draw()
rend = fig.canvas.get_renderer()
px_to_pt = 72.0 / fig.dpi
MAX_SHIFT = 34.0                       # punten; verder weg wordt het label misleidend

for _ in range(80):
    boxes = [a.get_window_extent(rend).expanded(1.04, 1.25) for a in artists]
    botsingen = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            bi, bj = boxes[i], boxes[j]
            if not (bi.x0 < bj.x1 and bj.x0 < bi.x1
                    and bi.y0 < bj.y1 and bj.y0 < bi.y1):
                continue
            botsingen += 1
            duw = (min(bi.y1, bj.y1) - max(bi.y0, bj.y0)) / 2 * px_to_pt + 0.4
            boven, onder = (i, j) if bi.y0 > bj.y0 else (j, i)
            offsets[boven][1] += duw
            offsets[onder][1] -= duw
    if not botsingen:
        break
    for k, a in enumerate(artists):
        offsets[k][1] = max(-MAX_SHIFT, min(MAX_SHIFT, offsets[k][1]))
        a.set_position(tuple(offsets[k]))
    fig.canvas.draw()

# Definitief opnieuw tekenen, nu met een verwijslijntje voor wat verschoven is
for a in artists:
    a.remove()
verschoven = 0
for (t, p), (dx, dy) in zip(anchors, offsets):
    leader = abs(dy) > 5.0
    verschoven += leader
    _label(t, p, dx, dy, leader)
print(f"labels met verwijslijntje: {verschoven}")

style_map(ax, "Gebiedsindeling — Rotterdam",
          subtitle="de 21 gebieden van de gemeente")
finalize_map(fig, source="Gemeente Rotterdam via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

# Invariant 4: ook een referentiekaart heeft een legenda. Eén klasse volstaat hier,
# want alle vlakken zijn gelijkwaardig — de legenda benoemt wat een vlak ís.
add_swatch_legend(ax, [VULLING], ["Gebied"], title="Legenda", corner="auto",
                  fontsize=9)

for w in validate_map(fig, ax, data=gebieden):
    print("WARN:", w)

print(save_map(fig, "gebiedsindeling_rotterdam"))
