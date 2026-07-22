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
labels op de centroïde botsen. `add_area_labels` (library) duwt overlappende labels
verticaal uit elkaar en geeft elk label dat noemenswaardig opschuift een verwijslijntje
naar zijn eigen gebied. In de praktijk zijn dat er 5.

De gebiedsgrenzen zijn donkerder en dikker dan de STYLE-default: op een gekleurde
basemap vallen ze anders weg tegen de wegen, en hier is de grens het onderwerp.

Bron: TIR-gebieden via diensten.rotterdam.nl.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt

from rotterdam import (
    add_area_labels, add_rotterdam_basemap, add_swatch_legend, finalize_map,
    fit_figure_to_data, load_layer, save_map, setup_headless_matplotlib,
    style_map, validate_map,
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

# Gebiedsnamen op de kaart; de helper duwt botsende labels uit elkaar en zet een
# verwijslijntje bij wat verschoven is (zie add_area_labels). Vóór finalize_map.
verschoven = add_area_labels(ax, gebieden, "GEBDNAAM", fontsize=LABEL_FS)
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
