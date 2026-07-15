"""Kaart van Rotterdam met alle buurten (TIR-buurtindeling).

Gemaakt met de rotterdam-geoai skill. Buurten gekleurd per TIR-gebied zodat de
91 buurten leesbaar groeperen; witte buurtgrenzen, donkere gemeentegrens.
"""
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from matplotlib.transforms import ScaledTranslation

from rotterdam import (
    load_layer, style_map, finalize_map, fit_figure_to_data,
    add_swatch_legend_sidepanel, save_map, validate_map, STYLE,
)

# 1. Data — TIR-buurten (officiele Rotterdamse buurtindeling)
buurten = load_layer("buurten")
gemeente = load_layer("gemeente")
print(f"{len(buurten)} buurten in {buurten['GEBDNAAM'].nunique()} gebieden")

# 2. Kleur per gebied (categorisch), alfabetisch zodat legenda en kaart matchen
gebieden = sorted(buurten["GEBDNAAM"].unique())
# 21 gebieden > 20 kleuren in tab20: combineer tab20 + tab20b voor distinct kleuren
_swatches = list(cm.tab20.colors) + list(cm.tab20b.colors)
palette = [mcolors.to_hex(_swatches[i]) for i in range(len(gebieden))]
kleur_van = dict(zip(gebieden, palette))
buurten["_kleur"] = buurten["GEBDNAAM"].map(kleur_van)

# 3. Tekenen
fig, ax = plt.subplots(figsize=(13, 9))
buurten.plot(ax=ax, color=buurten["_kleur"], edgecolor="white", linewidth=0.4)
gemeente.boundary.plot(ax=ax, color="#333333", linewidth=1.0)
ax.set_aspect("equal")

# 4. Kaartelementen: titel + noordpijl (linksboven). De subtitel plaats ik zelf
#    net boven de kaartrand (va="bottom") i.p.v. via subtitle= van style_map, zodat
#    er een duidelijke marge tussen subtitel en kaart zit i.p.v. eroverheen.
titel = f"Rotterdam — alle buurten (n = {len(buurten)})"
style_map(ax, titel)
ax.set_title(titel, loc="left", pad=30,
             fontsize=STYLE["title_size"], fontweight=STYLE["title_weight"],
             color=STYLE["title_color"])
_marge_omhoog = ScaledTranslation(0, 8 / 72, fig.dpi_scale_trans)  # 8 pt boven de kaartrand
ax.text(0.0, 1.0, "TIR-buurtindeling, gekleurd per gebied",
        transform=ax.transAxes + _marge_omhoog, va="bottom",
        fontsize=STYLE["subtitle_size"], color=STYLE["subtitle_color"],
        weight=STYLE["subtitle_weight"])

# 5. Footer (bron + AI-disclaimer + uitgever) en figuur op de gebiedsvorm passen
finalize_map(fig, source="TIR via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

# 6. Kleurstaal-legenda per gebied. 21 gebieden passen in geen enkele hoek/rand,
#    dus in een zijpaneel rechts van de kaart (invariant 8). Het paneel wordt
#    precies zo breed als de legenda + marge -> geen witruimte ernaast.
add_swatch_legend_sidepanel(
    fig, ax, palette, gebieden,
    title="Legenda", legendakop="Gebied", fontsize=8,
)

# 7. Valideren + opslaan
warns = validate_map(fig, ax, data=buurten)
if warns:
    print("Waarschuwingen:", *warns, sep="\n  - ")

path = save_map(fig, "rotterdam_alle_buurten")
print("Kaart opgeslagen:", path)
