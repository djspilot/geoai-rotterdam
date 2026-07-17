"""Regressietests voor de rotterdam-kaartconventies.

Plain asserts (geen pytest nodig). Draai met de project-venv:
    .venv/Scripts/python.exe "General data/tests/test_conventies.py"

Vangt regressies af zoals: per ongeluk de style_map-defaults wijzigen, de
variant-defaults omzetten, of validate_map-checks slopen.
"""
import inspect
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # General data
warnings.simplefilter("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from rotterdam import (
    load_layer, style_map, finalize_map, place_legend, validate_map,
    add_north_arrow, add_scalebar, add_proportional_legend, choropleth,
)

_failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        _failures.append(name)


# 1. Defaults: noordpijl/schaalstok standaard uit, variant B standaard
check("add_north_arrow variant default = B",
      inspect.signature(add_north_arrow).parameters["variant"].default == "B")
check("add_scalebar variant default = B",
      inspect.signature(add_scalebar).parameters["variant"].default == "B")
_sp = inspect.signature(style_map).parameters
check("style_map north default = False", _sp["north"].default is False)
check("style_map scalebar default = False", _sp["scalebar"].default is False)
check("style_map north_variant default = B", _sp["north_variant"].default == "B")
check("style_map scalebar_variant default = B", _sp["scalebar_variant"].default == "B")

# 2. Golden map: correcte kaart geeft geen validate-waarschuwingen
gem = load_layer("gemeente")
fig, ax = plt.subplots(figsize=(8, 8))
gem.boundary.plot(ax=ax, color="#333")
style_map(ax, "Testkaart", subtitle="ondertitel")
finalize_map(fig, source="TIR via diensten.rotterdam.nl")
place_legend(ax, [Line2D([0], [0], color="#333", label="Grens")], ["Grens"], corner="auto")
check("golden map: validate_map schoon", validate_map(fig, ax, data=gem) == [])
plt.close(fig)

# 3. validate_map vangt fouten: geen bron, niet-vette titel, Engelse getalnotatie
fig2, ax2 = plt.subplots(figsize=(8, 8))
gem.boundary.plot(ax=ax2, color="#333")
ax2.set_title("Niet vet", loc="left", fontweight="normal")
ax2.set_axis_off()
ax2.text(0.0, 1.0, "20,028 inw", transform=ax2.transAxes, color="#555555")
_w = validate_map(fig2, ax2)
check("validate vangt: geen bronvermelding", any("bronvermelding" in x for x in _w))
check("validate vangt: hoofdtitel niet vet", any("niet vetgedrukt" in x for x in _w))
check("validate vangt: NL-getalnotatie", any("getalnotatie" in x for x in _w))
plt.close(fig2)

# 4. Choropleet (genormaliseerde waarde): geen normalisatie-/bron-waarschuwing
buurten = load_layer("buurten").copy()
buurten["waarde"] = range(1, len(buurten) + 1)          # dummy genormaliseerd getal
figc, axc = choropleth(buurten, "waarde", title="Choropleet-test",
                       legend_label="eenheid", scheme="quantiles", k=5)
finalize_map(figc, source="TIR via diensten.rotterdam.nl")
_wc = validate_map(figc, axc, data=buurten, normalized=True)
check("choropleth: geen normalisatie-warning", not any("normalisatie" in x for x in _wc))
check("choropleth: bronvermelding aanwezig", not any("bronvermelding" in x for x in _wc))
plt.close(figc)

# 5. Proportionele-symbool legenda telt als legenda (geen ax.legend, wél gemarkeerd)
figp, axp = plt.subplots(figsize=(8, 8))
gem.boundary.plot(ax=axp, color="#333")
axp.scatter([gem.geometry.iloc[0].centroid.x], [gem.geometry.iloc[0].centroid.y], s=[100])
style_map(axp, "Proportioneel-test")
finalize_map(figp, source="TIR via diensten.rotterdam.nl")
add_proportional_legend(axp, values=[10, 50], sizes=[60, 300], corner="auto")
_wp = validate_map(figp, axp, data=gem)
check("proportionele legenda: geen 'geen legenda'-warning",
      not any("Geen legenda" in x for x in _wp))
plt.close(figp)

print()
if _failures:
    print(f"{len(_failures)} test(s) FAALDEN:", *_failures, sep="\n  - ")
    sys.exit(1)
print("Alle conventie-tests geslaagd.")
