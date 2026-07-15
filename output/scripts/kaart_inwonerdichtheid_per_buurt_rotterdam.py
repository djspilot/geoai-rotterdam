"""Choropleet van de inwonerdichtheid per buurt in Rotterdam.

Elke CBS-buurt gekleurd naar bevolkingsdichtheid (inwoners per km²). We gebruiken
het officiële CBS-veld `bevolkingsdichtheidInwonersPerKm2` (gebaseerd op het
*land*oppervlak), zodat havenwater de dichtheid niet verdunt — nauwkeuriger dan
delen door de geometrische oppervlakte.

- classificatie: 5 klassen met **natural breaks (Jenks)**, gehele grenzen;
- sequentieel kleurverloop geel→donkerrood (licht = laag, donker = hoog);
- legenda met `add_swatch_legend`: vet kopje "Legenda", daaronder de legendakop
  "Inwoners per km²" (eenheid), dan de klassen; auto-geplaatst (invariant 8);
- grijze basemap (esthetische keuze, neutrale onderlaag onder de vlakken).

Bron: CBS Wijk- en Buurtkaart 2024 (PDOK WFS).
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import matplotlib.pyplot as plt
import mapclassify

from rotterdam import (
    load_layer, cbs_buurten_rotterdam, style_map, add_scalebar,
    add_rotterdam_basemap, add_pdok_basemap, finalize_map, fit_figure_to_data,
    add_swatch_legend, save_map, setup_headless_matplotlib, RD_NEW, nl_getal,
)

setup_headless_matplotlib()

# --- data: álle Rotterdamse buurten (ook de lege haven-/industriebuurten) ----
DENS = "bevolkingsdichtheidInwonersPerKm2"
GEEN = "#d9d9d9"                                      # kleur 'geen gegevens'
alle = cbs_buurten_rotterdam(2024, drop_empty=False).to_crs(RD_NEW)
buurten = alle[alle[DENS] > 0].copy()                # met dichtheidswaarde
zonder = alle[~(alle[DENS] > 0)].copy()              # geen (geldige) waarde (o.a. -99997)
print(f"met waarde: {len(buurten)} | zonder waarde: {len(zonder)} | "
      f"dichtheid min/mediaan/max: {buurten[DENS].min():.0f} / "
      f"{buurten[DENS].median():.0f} / {buurten[DENS].max():.0f}")

# --- classificatie: 5 klassen, natural breaks (Jenks) -----------------------
# De klasse-indeling blijft op de échte Jenks-breaks; alleen de label-grenzen
# ronden we af naar ronde getallen voor de leesbaarheid.
k = 5
cls = mapclassify.classify(buurten[DENS].to_numpy(), "NaturalBreaks", k=k)
buurten["klasse"] = cls.yb


def round_nice(edges):
    """Rond grenzen af op de grofste ronde stap die ze strikt oplopend houdt."""
    for step in (1000, 500, 250, 100, 50, 10):
        r = [int(round(e / step)) * step for e in edges]
        if all(r[i] < r[i + 1] for i in range(len(r) - 1)):
            return r
    return [int(round(e)) for e in edges]


edges = round_nice([buurten[DENS].min()] + list(cls.bins))

labels = [f"{nl_getal(edges[i])} – {nl_getal(edges[i + 1])}" for i in range(k)]
cmap = plt.get_cmap("YlOrRd")
colors = [cmap((i + 0.5) / k) for i in range(k)]

# --- kaart ------------------------------------------------------------------
gemeente = load_layer("gemeente").to_crs(RD_NEW)

fig, ax = plt.subplots(figsize=(13, 11))
gemeente.plot(ax=ax, facecolor="none", edgecolor="#333333", linewidth=1.0, zorder=6)
if len(zonder):
    zonder.plot(ax=ax, facecolor=GEEN, edgecolor="#555555", linewidth=0.3,
                alpha=0.9, zorder=5)
for i in range(k):
    sub = buurten[buurten["klasse"] == i]
    if len(sub):
        sub.plot(ax=ax, facecolor=colors[i], edgecolor="#555555",
                 linewidth=0.3, alpha=0.9, zorder=5)

# grijze basemap (esthetische keuze). Invariant 12: eigen Rotterdam-basemap niet
# vermelden, PDOK-fallback (derde partij) wél.
bron_delen = ["CBS Wijk- en Buurtkaart 2024"]
try:
    add_rotterdam_basemap(ax, layer="grijs")
except Exception as e:
    print("fallback PDOK:", type(e).__name__)
    add_pdok_basemap(ax, layer="grijs")
    bron_delen.append("Basiskaart: PDOK BRT")

style_map(ax, "Inwonerdichtheid per buurt in Rotterdam")
# geen schaalstok: choropleet, afstand niet relevant (invariant 14)
finalize_map(fig, source=" · ".join(bron_delen), tight_bottom=True)
fit_figure_to_data(fig, ax)

# legenda ná fit_figure_to_data (definitieve figuurhoogte -> correcte plaatsing).
# 'Geen gegevens' als extra klasse; corner="auto" mijdt automatisch alle lagen
# — ook de buurt-VLAKKEN, dus de legenda landt buiten de bebouwing.
legend_colors = colors + [GEEN]
legend_labels = labels + ["Geen gegevens"]
add_swatch_legend(ax, colors=legend_colors, labels=legend_labels, title="Legenda",
                  legendakop="Inwoners per km²", corner="auto")

print("opgeslagen:", save_map(fig, "inwonerdichtheid_per_buurt_rotterdam"))
