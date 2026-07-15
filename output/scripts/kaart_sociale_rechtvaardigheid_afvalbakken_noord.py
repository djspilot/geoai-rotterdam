"""Sociale-rechtvaardigheidskaart Rotterdam Noord.

Twee-paneel: afvalbakken per 1000 inwoners (links) vs gemiddeld
gestandaardiseerd huishoudinkomen (rechts) per CBS-buurt in Noord.
Inset toont scatter + Pearson correlatie tussen beide.

Welvaarts-indicator: % personen met laag inkomen per CBS-buurt (CBS 2023,
2024 nog niet gepubliceerd voor Rotterdam). Hoger = armer.

Vraag: krijgen armere buurten in Noord evenveel afvalbak-dekking als
welvarende buurten? Positieve correlatie (r > 0) tussen %laag-inkomen en
afvalbakken/1000inw = arme buurten meer dekking (corrigeerend). Negatieve
(r < 0) = welvarende buurten meer dekking (ongelijk). Bij ~0 = neutraal.
"""

from __future__ import annotations

import sys
from urllib.parse import urlencode

sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rotterdam import (
    DATA_OUT,
    MAPS_DIR,
    RD_NEW,
    ROTTERDAM_NOORD_GEBIEDEN,
    finalize_map,
    load_layer,
    place_legend,
    save_map,
    style_map,
    validate_map,
)
from rotterdam.cartography import setup_headless_matplotlib

setup_headless_matplotlib()

INCOME_COL = "percentagePersonenMetLaagInkomen"
POP_COL = "aantalInwoners"
CBS_YEAR = 2023  # 2024 heeft nog geen Rotterdam-inkomenscijfers

# 1. Rotterdam Noord polygon
gebieden = load_layer("gebieden")
noord = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_NOORD_GEBIEDEN)].copy()
noord_union = noord.dissolve().geometry.iloc[0]

# 2. CBS buurten (income + bevolking) — CQL_FILTER wordt door deze WFS
# genegeerd. Gebruik bbox + client-side filter op gemeentenaam.
xmin, ymin, xmax, ymax = noord.total_bounds
pad = 2000  # 2 km buffer rond Noord-bbox
url = f"https://service.pdok.nl/cbs/wijkenbuurten/{CBS_YEAR}/wfs/v1_0?" + urlencode({
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "typeNames": "wijkenbuurten:buurten", "outputFormat": "application/json",
    "count": "5000",
    "bbox": f"{xmin-pad},{ymin-pad},{xmax+pad},{ymax+pad},EPSG:28992",
})
cbs = gpd.read_file(url).to_crs(RD_NEW)
cbs = cbs[cbs["gemeentenaam"] == "Rotterdam"].copy()
cbs[INCOME_COL] = pd.to_numeric(cbs[INCOME_COL], errors="coerce")
cbs[POP_COL] = pd.to_numeric(cbs[POP_COL], errors="coerce")
# CBS-geheimhouding = negatieve sentinel-waarden (-99997, -99999999)
cbs = cbs[(cbs[POP_COL] > 0) & (cbs[INCOME_COL] >= 0) & (cbs[INCOME_COL] <= 100)].copy()

# Keep CBS-buurten waarvan centroid in Noord ligt
cbs_noord = cbs[cbs.geometry.centroid.within(noord_union)].copy()

# 3. Afvalbakken in Noord, koppelen aan CBS-buurt
afval = load_layer("afvalbak")
afval_noord = afval[afval.geometry.within(noord_union)].copy()

joined = gpd.sjoin(afval_noord, cbs_noord[["buurtcode", "geometry"]],
                   how="inner", predicate="within")
counts = joined.groupby("buurtcode").size().rename("n_afvalbak")
cbs_noord = cbs_noord.merge(counts, left_on="buurtcode", right_index=True, how="left")
cbs_noord["n_afvalbak"] = cbs_noord["n_afvalbak"].fillna(0).astype(int)
cbs_noord["afvalbak_per_1000"] = cbs_noord["n_afvalbak"] / cbs_noord[POP_COL] * 1000

# Toplijn-statistieken
n_buurten = len(cbs_noord)
total_bakken = int(cbs_noord["n_afvalbak"].sum())
total_inw = int(cbs_noord[POP_COL].sum())
mediaan_laag_inkomen = cbs_noord[INCOME_COL].median()
gem_dichtheid = cbs_noord["afvalbak_per_1000"].mean()

# Correlatie
mask = cbs_noord["afvalbak_per_1000"].notna() & cbs_noord[INCOME_COL].notna()
sub = cbs_noord.loc[mask, ["afvalbak_per_1000", INCOME_COL]]
# strip outliers boven 99e percentiel om as leesbaar te houden
p99 = sub["afvalbak_per_1000"].quantile(0.99)
sub_plot = sub[sub["afvalbak_per_1000"] <= p99]
corr = sub["afvalbak_per_1000"].corr(sub[INCOME_COL])

# 4. Plot — 2 panelen + scatter inset. Figuurhoogte volgt de brede/lage vorm van
#    Noord (aspect ~1.46), zodat de kaarten de figuur vullen zonder verticale witruimte.
fig, axes = plt.subplots(1, 2, figsize=(16, 7.4), constrained_layout=False)

noord_border = noord.boundary

# Panel 1: afvalbakken per 1000 inwoners
ax1 = axes[0]
vmax_left = cbs_noord["afvalbak_per_1000"].quantile(0.95)
cbs_noord.plot(
    ax=ax1, column="afvalbak_per_1000", cmap="YlOrRd",
    scheme="quantiles", k=5, legend=True,
    legend_kwds={"title": "afvalbakken / 1000 inw", "loc": "lower left",
                 "fontsize": 8, "title_fontsize": 9, "frameon": True},
    edgecolor="white", linewidth=0.3,
)
noord_border.plot(ax=ax1, color="black", linewidth=1.0)
style_map(ax1, "Afvalbak-dichtheid",
          subtitle=f"per CBS-buurt, n={n_buurten} buurten")

# Panel 2: % personen met laag inkomen (donker = armer)
ax2 = axes[1]
cbs_noord.plot(
    ax=ax2, column=INCOME_COL, cmap="Purples",
    scheme="quantiles", k=5, legend=True,
    legend_kwds={"title": "% personen met\nlaag inkomen",
                 "loc": "lower left", "fontsize": 8, "title_fontsize": 9,
                 "frameon": True, "fmt": "{:.0f}"},
    edgecolor="white", linewidth=0.3,
)
noord_border.plot(ax=ax2, color="black", linewidth=1.0)
style_map(ax2, "Armoede-aandeel",
          subtitle=f"mediaan {mediaan_laag_inkomen:.0f}% per buurt")

# Scatter inset linksonder op ax1 (over de data; opaque achtergrond). Zo blijft de
# datavrije hoek rechtsonder vrij voor de legenda (die de data moet ontwijken).
inset = ax1.inset_axes([0.06, 0.07, 0.33, 0.29])
inset.scatter(sub_plot[INCOME_COL], sub_plot["afvalbak_per_1000"],
              s=10, alpha=0.55, color="#444")
# trendlijn
if len(sub_plot) >= 5:
    coef = np.polyfit(sub_plot[INCOME_COL], sub_plot["afvalbak_per_1000"], 1)
    xs = np.linspace(sub_plot[INCOME_COL].min(), sub_plot[INCOME_COL].max(), 30)
    inset.plot(xs, coef[0]*xs + coef[1], color="#c0392b", linewidth=1.4)
inset.set_xlabel("% laag inkomen", fontsize=7)
inset.set_ylabel("bakken/1000inw", fontsize=7)
inset.set_title(f"correlatie r = {corr:+.2f}", fontsize=8)
inset.tick_params(labelsize=6)
inset.set_facecolor("#fafafa")

interpretatie = (
    "r > 0: armere buurten meer bakken (corrigeerend).  "
    "r < 0: welvarende buurten meer bakken (ongelijk)."
)

finalize_map(
    fig,
    source=f"Obsurv (afvalbakken) + CBS Wijk- en Buurtkaart {CBS_YEAR} (inkomen, inwoners)",
    date="2026-05-27",
    suptitle="Sociale rechtvaardigheid: afvalbak-dekking vs armoede — Rotterdam Noord",
    suptitle_subtitle=interpretatie,
)

# geopandas plaatst de legenda vast, óver de data. Herplaats beide legenda's
# consistent naar de datavrije hoek rechtsonder (invariant 8, compacte fontsize),
# met dezelfde swatches; ná finalize_map. De scatter-inset (paneel 1) staat
# linksonder over de data en wordt door de legenda ontweken.
from shapely.geometry import box as _box  # noqa: E402


def _relocate_legend(ax, avoid=None, corner="lower right", fontsize=8):
    leg = ax.get_legend()
    if leg is None:
        return
    handles = list(leg.legend_handles)
    labels = [t.get_text() for t in leg.get_texts()]
    title = leg.get_title().get_text()
    leg.remove()
    place_legend(ax, handles, labels, title=title, corner=corner, data=avoid,
                 fontsize=fontsize)


_ix0, _iy0 = ax1.get_xlim()[0], ax1.get_ylim()[0]
_iw = ax1.get_xlim()[1] - _ix0
_ih = ax1.get_ylim()[1] - _iy0
_inset_box = _box(_ix0 + 0.03 * _iw, _iy0 + 0.05 * _ih,
                  _ix0 + 0.41 * _iw, _iy0 + 0.38 * _ih)
_relocate_legend(ax1, avoid=gpd.GeoSeries([_inset_box], crs=RD_NEW))
_relocate_legend(ax2, avoid=None)

warns = validate_map(fig, axes[0], data=cbs_noord, normalized=True)
for w in warns:
    print("WARN:", w)

out = save_map(fig, "sociale_rechtvaardigheid_afvalbakken_noord")
print(f"map saved -> {out}")

# 5. Csv export voor toplijn-tabel
csv_path = DATA_OUT / "sociale_rechtvaardigheid_afvalbakken_noord.csv"
cbs_noord[["buurtcode", "buurtnaam", POP_COL, "n_afvalbak",
           "afvalbak_per_1000", INCOME_COL]].sort_values(
    "afvalbak_per_1000", ascending=False
).to_csv(csv_path, index=False)
print(f"csv saved  -> {csv_path}")

print()
print("=== Topregels ===")
print(f"Buurten in Noord met inkomen+inwoners: {n_buurten}")
print(f"Totaal afvalbakken: {total_bakken:,}")
print(f"Totaal inwoners:    {total_inw:,}")
print(f"Gem. dichtheid:     {gem_dichtheid:.2f} bakken / 1000 inw")
print(f"Mediaan % laag ink: {mediaan_laag_inkomen:.1f}%")
print(f"Correlatie (Pearson r): {corr:+.3f}")
