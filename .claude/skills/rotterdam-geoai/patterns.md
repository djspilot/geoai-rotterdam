# Runnable Patterns

Each block assumes:

```python
import sys; sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")
from rotterdam import *  # constants + helpers
import matplotlib.pyplot as plt
```

## 1. Statische point map per gebied

```python
gebieden = load_layer("gebieden")
afval    = load_layer("afvalbak")
zuid     = filter_to_area(afval, gebieden, gebied_names=ROTTERDAM_ZUID_GEBIEDEN)

zuid_polys = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_ZUID_GEBIEDEN)]
fig, ax = point_map(zuid, boundary=zuid_polys,
                    title="Afvalbakken in Rotterdam Zuid",
                    asset="afvalbak", markersize=4)
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "afvalbakken_rotterdam_zuid")
```

## 2. Choropleth — afvalbakken per buurt, genormaliseerd op inwonertal (CBS)

```python
buurten_cbs = cbs_buurten_rotterdam(year=2024)
afval = load_layer("afvalbak")

# Tel per CBS-buurt en normaliseer
out = count_per_polygon(
    afval, buurten_cbs,
    key="buurtnaam", normalize_by="aantal_inwoners", per=1000,
)
fig, ax = choropleth(out, "rate",
                     title="Afvalbakken per 1000 inwoners",
                     legend_label="per 1000 inw.")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "afvalbakken_per_1000_inwoners")
```

## 3. Hexbin voor 100k+ punten

```python
bomen    = load_layer("bomen")
gemeente = load_layer("gemeente")

fig, ax = plt.subplots(figsize=(12, 12))
gemeente.boundary.plot(ax=ax, color="#444", linewidth=0.8)
ax.hexbin(bomen.geometry.x, bomen.geometry.y,
          gridsize=80, cmap="YlGn", mincnt=1)
style_map(ax, "Boomdichtheid Rotterdam (hexbin)")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "bomen_hexbin")
```

## 4. Adres → coördinaat → buffer-query

```python
xy = pdok_geocode_rd("Coolsingel 40, Rotterdam")
from shapely.geometry import Point
buffer_500m = Point(xy).buffer(500)

afval = load_layer("afvalbak")
in_buffer = afval[afval.intersects(buffer_500m)]
print(len(in_buffer), "afvalbakken binnen 500m van Coolsingel 40")
```

## 5. Live download vanaf ArcGIS REST (paginated)

```python
data = fetch_arcgis_layer(
    ARCGIS_LAYERS["lichtpunten"],
    where="WOONPLAATS='Rotterdam'",
)
import json
(OUT / "lichtpunten_rotterdam.geojson").write_text(json.dumps(data))
```

## 6. Folium met MarkerCluster (alléén op verzoek)

```python
import folium
from folium.plugins import MarkerCluster

afval_wgs = load_layer("afvalbak").to_crs(WGS84)
m = folium.Map(location=ROTTERDAM_CENTER_WGS, zoom_start=12,
               tiles="CartoDB positron")
cluster = MarkerCluster().add_to(m)
for _, r in afval_wgs.iterrows():
    folium.CircleMarker([r.geometry.y, r.geometry.x], radius=2,
                        color=ASSET_COLORS["afvalbak"], fill=True).add_to(cluster)
m.save(str(OUT / "afval_cluster.html"))
```

## 7. Statische kaart met PDOK basemap

```python
buurten = load_layer("buurten")
afval   = load_layer("afvalbak")
fig, ax = plt.subplots(figsize=(12, 12))
buurten.plot(ax=ax, facecolor="none", edgecolor="#666", linewidth=0.5)
afval.plot(ax=ax, color=ASSET_COLORS["afvalbak"], markersize=2, alpha=0.7)
add_pdok_basemap(ax, layer="grijs")
style_map(ax, "Afvalbakken Rotterdam", subtitle="bron: Obsurv via diensten.rotterdam.nl")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "afval_met_basemap")
```

## End-to-end: operationele vraag

> "Waar zijn afvalbakken oververtegenwoordigd in Rotterdam? Maak een kaart en geef me drie buurten om naar te kijken."

**Stappen die de agent neemt:**

1. Laden + normaliseren — counts alleen zegt niets, vraag is *oververtegenwoordigd* dus per inwoner.
2. Choropleet maken met diverging palette rond de stedelijke mediaan.
3. Top-3 afwijkers extraheren als concrete handvatten.
4. Valideren tegen richtlijnen.

```python
import sys; sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")
from rotterdam import *
import matplotlib.pyplot as plt

# 1. Data + normalisatie
cbs   = cbs_buurten_rotterdam(year=2024)
afval = load_layer("afvalbak")
out   = count_per_polygon(afval, cbs,
                          key="buurtnaam", normalize_by="aantal_inwoners", per=1000)

# Afwijking van de stedelijke mediaan (diverging interpretatie)
median = out["rate"].median()
out["afwijking"] = out["rate"] - median

# 2. Kaart
fig, ax = choropleth(out, "afwijking",
                     title="Afvalbakken per 1000 inwoners — afwijking van mediaan",
                     cmap="RdBu_r", scheme="quantiles", k=5,
                     legend_label=f"Δ t.o.v. mediaan ({median:.1f})")
path = finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "afval_afwijking_mediaan")

# 3. Top-3 oververtegenwoordigd
top3 = out.nlargest(3, "rate")[["buurtnaam", "n", "aantal_inwoners", "rate"]]
print("Sterkst oververtegenwoordigd:")
for _, r in top3.iterrows():
    print(f"  - {r.buurtnaam}: {int(r.n)} afvalbakken / {int(r.aantal_inwoners)} inw "
          f"= {r.rate:.1f} per 1000")

# 4. Validatie
warns = validate_map(fig, ax, data=out, normalized=True, n_classes=5)
if warns: print("\nWaarschuwingen:", *warns, sep="\n  - ")
```

**Antwoord aan gebruiker** (3 bullets + kaart):
- Top-3 buurten gerapporteerd met absolute en relatieve cijfers
- Definitie "oververtegenwoordigd" vermeld (per 1000 inwoners, t.o.v. stedelijke mediaan)
- Kaart-pad: `output/afval_afwijking_mediaan.png`

## End-to-end: rapport voor wethouder

> "Maak een briefkaart voor de wethouder over de bomen in Charlois — context, verdeling, en één visueel hoofdpunt."

**Stappen:**

1. Filter bomen op Charlois via spatial join (sneller dan attribuutfilter, geen vervuiling).
2. Twee panelen: locatiekaart (links) + soort-verdeling top 5 (rechts).
3. Eén pagina-titel + bronvermelding + datum.
4. Output naar PNG geschikt voor printen.

```python
import sys; sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")
from rotterdam import *
import matplotlib.pyplot as plt
from datetime import date

# 1. Data
gebieden = load_layer("gebieden")
bomen    = load_layer("bomen")
charlois_poly = gebieden[gebieden["GEBDNAAM"] == "Charlois"]
bomen_charlois = filter_to_area(bomen, gebieden, gebied_names=["Charlois"])

# Detecteer soortkolom robuust (varieert per export)
soort_col = next((c for c in ["BOOMSORTIMENT_NEDERLANDS", "SOORT_NL", "SOORTNAAM"]
                  if c in bomen_charlois.columns), None)

# 2. Layout
fig = plt.figure(figsize=(14, 9))
ax_map = fig.add_subplot(1, 2, 1)
ax_bar = fig.add_subplot(1, 2, 2)

charlois_poly.plot(ax=ax_map, facecolor="#f6f3ee", edgecolor="#8c8377", linewidth=0.8)
bomen_charlois.plot(ax=ax_map, color=ASSET_COLORS["bomen"], markersize=0.5, alpha=0.5)
style_map(ax_map, f"Bomen in Charlois (n = {len(bomen_charlois):,})")

if soort_col:
    top = (bomen_charlois[soort_col].fillna("Onbekend")
           .value_counts().head(5).iloc[::-1])
    ax_bar.barh(top.index, top.values, color=ASSET_COLORS["bomen"])
    ax_bar.set_title("Top 5 boomsoorten", loc="left", fontweight="bold")
    ax_bar.spines[["top", "right"]].set_visible(False)
else:
    ax_bar.text(0.5, 0.5, "Soortinformatie niet beschikbaar",
                ha="center", va="center", transform=ax_bar.transAxes)
    ax_bar.set_axis_off()

# 3. Pagina-titel en bronregel
fig.suptitle("Bomen in Charlois — briefkaart wethouder", fontsize=16, fontweight="bold", y=0.98)
fig.text(0.01, 0.01,
         f"Bron: Obsurv via diensten.rotterdam.nl • TIR-gebied Charlois • {date.today().isoformat()}",
         fontsize=8, color="#666")

# 4. Output + validatie
path = finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "briefkaart_bomen_charlois")
warns = validate_map(fig, ax_map, data=bomen_charlois)
if warns: print("Waarschuwingen:", *warns, sep="\n  - ")
print(f"\nGeschreven: {path}")
```

**Antwoord aan gebruiker:**
- Totaalaantal bomen in Charlois
- Top-3 soorten met aandeel
- Bronvermelding + datum staan op de plaat
- Bestand klaar voor inleveren

## 8a. Hybride — adres → BAG-detail → buffer-analyse op Obsurv

Geverifieerd werkend (integratie-test 2026-05-26). MCP voor *adres-resolutie + BAG-kenmerken*, `rotterdam` package voor *Obsurv-data + cartografie*.

**Voorbeeld**: *"Wat voor pand is Coolsingel 40 en welke afvalbakken/lichtpunten staan binnen 200m?"*

```
Agent stap 1 (MCP, in dialoog):
  → bag_address_detail(query="Coolsingel 40, Rotterdam")
  → records[0].data heeft: pdok_id, gemeentenaam, postcode,
       (mogelijk) oppervlakte_m2, bouwjaar, gebruiksdoelen
  → check op null voordat je waarden citeert
  → noteer pdok_id voor stap 2
```

```python
# Agent stap 2 (Python, reproduceerbaar):
import sys; sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")
from rotterdam import *
from shapely.geometry import Point

# Coord via standalone pdok-MCP of geocode-helper (MCP gaf pdok_id; helper geeft RD)
x, y = pdok_geocode_rd("Coolsingel 40, Rotterdam")
buffer_200m = Point(x, y).buffer(200)

afval = load_layer("afvalbak")
licht = load_layer("lichtpunten_stadsdriehoek")
afval_in = afval[afval.intersects(buffer_200m)]
licht_in = licht[licht.intersects(buffer_200m)]

# Mini-kaart
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9, 9))
import geopandas as gpd
gpd.GeoSeries([buffer_200m], crs=RD_NEW).plot(ax=ax, facecolor="none",
                                              edgecolor="#888", linewidth=1)
afval_in.plot(ax=ax, color=ASSET_COLORS["afvalbak"], markersize=20, label="afvalbak")
licht_in.plot(ax=ax, color=ASSET_COLORS["lichtpunten"], markersize=10, label="lichtpunt")
ax.plot(x, y, "k*", markersize=12, label="Coolsingel 40")
ax.legend()
style_map(ax, "Assets binnen 200m van Coolsingel 40",
          subtitle=f"{len(afval_in)} afvalbakken, {len(licht_in)} lichtpunten")
finalize_map(fig, source="BAG via NL-GOV-MCP + Obsurv via diensten.rotterdam.nl")
save_map(fig, "coolsingel40_assets_200m")
```

**Antwoord aan gebruiker** (3 regels):
- Pand-type uit BAG (`gebruiksdoelen`) als niet-null, anders: "Kadaster-detail niet beschikbaar voor dit verblijfsobject"
- N afvalbakken + N lichtpunten binnen 200m
- Kaart-pad

## 8b. Hybride — ruimtelijke plannen overlay op TIR-gebied

Werkend pattern voor planologie-context.

**Voorbeeld**: *"Welke vigerende bestemmingsplannen zijn er in Charlois en hoe verhouden ze zich tot de buurten?"*

```
Agent stap 1 (MCP):
  → ruimtelijke_plannen_search(gemeente="Rotterdam", status="vigerend", rows=50)
  → records bevatten: IMRO-id, naam, planType, status, viewer-URL
  → géén geometry in response → voor kaart-overlay haal je de WMS-tiles
    via de viewer-URL of plot je plan-id-labels op TIR-buurten
```

```python
# Agent stap 2 (Python):
import sys; sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")
from rotterdam import *
import matplotlib.pyplot as plt

gebieden = load_layer("gebieden")
buurten  = load_layer("buurten")
charlois_poly = gebieden[gebieden["GEBDNAAM"] == "Charlois"]
charlois_buurten = buurten[buurten["GEBDNAAM"] == "Charlois"]

# Plan-overzicht in tekst, kaart toont alleen TIR-context
fig, ax = plt.subplots(figsize=(10, 10))
charlois_poly.plot(ax=ax, facecolor="#f6f3ee", edgecolor="#8c8377", linewidth=1)
charlois_buurten.plot(ax=ax, facecolor="none", edgecolor="#aa9", linewidth=0.5)
add_pdok_basemap(ax, layer="grijs")
style_map(ax, "Charlois — TIR-buurten",
          subtitle="Bestemmingsplannen: zie tekst-output")
finalize_map(fig, source="TIR + Ruimtelijke plannen via NL-GOV-MCP")
save_map(fig, "charlois_buurten_voor_plan_overlay")
```

**Tekst-output bij kaart**:
- Lijst van plannen met `naam` + `viewer-URL` (klikbaar) per plan
- Filter optie: groepeer op `planType` (bestemmingsplan / parapluherziening / etc.)
- Status-noot: alleen vigerende plannen getoond

**Regel**: MCP-output altijd opslaan in `General data/external/` met bron-vermelding zodat de pipeline reproduceerbaar blijft zonder de MCP-call te herhalen. Vermijd MCP-tools die `null`-velden geven of waarvan de coords ontbreken (`luchtmeetnet_latest` geeft `location: {0,0}` — zie `mcp_notes.md` "Bekende beperkingen").

## 8. Vergelijking twee gebieden (side-by-side)

```python
gebieden = load_layer("gebieden")
afval    = load_layer("afvalbak")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))
for ax, naam in zip(axes, ["Rotterdam Centrum", "Hillegersberg-Schiebroek"]):
    poly = gebieden[gebieden["GEBDNAAM"] == naam]
    inside = afval[afval.within(poly.union_all())]
    poly.plot(ax=ax, facecolor="#f6f3ee", edgecolor="#8c8377", linewidth=0.6)
    inside.plot(ax=ax, color=ASSET_COLORS["afvalbak"], markersize=3)
    style_map(ax, naam)
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl"); save_map(fig, "vergelijking_centrum_hillegersberg")
```

## 9. Categorische overzichtskaart met kleurstaal-legenda in een zijpaneel

Bv. "kaart van alle buurten": vlakken gekleurd per categorie (hier per gebied). Bij veel
categorieën past de kleurstaal-legenda in geen hoek/rand → gebruik
`add_swatch_legend_sidepanel`. Die maakt het zijpaneel **precies zo breed als de legenda +
marge**, dus de totale figuurbreedte = kaart + gap + legenda + marge (geen witruimte ernaast).
Roep aan **ná** `finalize_map` + `fit_figure_to_data`.

```python
import matplotlib.cm as cm, matplotlib.colors as mcolors

buurten  = load_layer("buurten")
gemeente = load_layer("gemeente")

# Kleur per gebied (categorisch). >20 categorieën? Combineer tab20 + tab20b.
gebieden = sorted(buurten["GEBDNAAM"].unique())
_sw = list(cm.tab20.colors) + list(cm.tab20b.colors)
palette = [mcolors.to_hex(_sw[i]) for i in range(len(gebieden))]
buurten["_kleur"] = buurten["GEBDNAAM"].map(dict(zip(gebieden, palette)))

fig, ax = plt.subplots(figsize=(13, 9))
buurten.plot(ax=ax, color=buurten["_kleur"], edgecolor="white", linewidth=0.4)
gemeente.boundary.plot(ax=ax, color="#333333", linewidth=1.0)
ax.set_aspect("equal")

style_map(ax, f"Rotterdam — alle buurten (n = {len(buurten)})")
finalize_map(fig, source="TIR via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

add_swatch_legend_sidepanel(fig, ax, palette, gebieden,
                            title="Legenda", legendakop="Buurten per gebied", fontsize=8)
save_map(fig, "rotterdam_alle_buurten")
```

## 10. Vrije paneelinhoud (naamlijst e.d.) zonder witruimte — `fit_side_panel`

Voor een zijpaneel met **eigen inhoud** (bv. een genummerde naamlijst, of een
matplotlib-`legend` + lijst) is er geen kant-en-klare helper. Teken de inhoud in
een ruim `add_side_panel` en roep dáárna `fit_side_panel(fig, ax, panel)` aan: die
krimpt het paneel tot de werkelijk getekende inhoud + marge. Nodig omdat
`save_map`'s `bbox_inches="tight"` de **volle paneel-as** meerekent (een onzichtbaar
achtergrondvlak verandert dat niet) en de footer tot ~0.95 van de figuurbreedte loopt.

```python
finalize_map(fig, source="…"); fit_figure_to_data(fig, ax)

panel = add_side_panel(fig, ax, width_in=4.0)     # ruim; wordt straks gekrompen
panel.text(0.0, 1.0, "Wijken", fontweight="bold", va="top", ha="left")
for i, (nr, naam) in enumerate(rows):             # eigen lay-out (fracties)
    y = 0.95 - i * lh
    panel.text(0.02, y, f"{nr}", ha="right", va="top", fontsize=7, fontweight="bold")
    panel.text(0.04, y, naam, ha="left",  va="top", fontsize=7)

fit_side_panel(fig, ax, panel)                    # paneel tot inhoud + marge krimpen
save_map(fig, "…")
```

## 11. Proportionele symbolen — absoluut aantal per buurt

Het alternatief voor een choropleet bij een "per buurt"-vraag. De **cirkeloppervlakte**
draagt de waarde, niet het vlak — daarom zijn **absolute aantallen hier correct** en geldt
de normalisatie-eis (invariant 3) niet. Kies dit als de gebruiker de *aantallen* wil zien;
kies een choropleet als het om *dichtheid* gaat. Zie de gekoppelde intake-vraag in
`intake.md` (punt 5).

Er is geen kant-en-klare `proportional_map()`; bouw hem uit `plt.subplots` +
`ax.scatter` + `add_proportional_legend`. Let op de volgorde: legenda **ná**
`finalize_map` + `fit_figure_to_data` (invariant 8).

```python
buurten = load_layer("buurten")
bomen   = load_layer("bomen")

per_buurt = count_per_polygon(bomen, buurten, key="TEKST")   # TEKST = TIR-code, uniek
per_buurt["n"] = per_buurt["n"].astype(int)

# s is een OPPERVLAK (pt²) -> s lineair in de waarde geeft straal ∝ √waarde: correct.
S_MAX = 620                    # stadsbreed op 91 buurten; groter => cirkels lopen in elkaar
nmax  = per_buurt["n"].max()
pts, sizes = [], []
for row, c in safe_centroids(per_buurt):
    if row["n"] <= 0:
        continue
    pts.append((c.x, c.y)); sizes.append(row["n"] / nmax * S_MAX)

fig, ax = plt.subplots(figsize=(12, 10))
per_buurt.plot(ax=ax, facecolor="none", edgecolor=STYLE["boundary_color"],
               linewidth=STYLE["boundary_width"], zorder=2)
add_rotterdam_basemap(ax, layer="kleur")
ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=sizes,
           facecolor=ASSET_COLORS["bomen"], edgecolor="#14512c",
           linewidth=0.6, alpha=0.65, zorder=3)

style_map(ax, "Aantal bomen per buurt — Rotterdam",
          subtitle="cirkeloppervlak evenredig aan het aantal bomen (Obsurv)")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl")
fit_figure_to_data(fig, ax)

# legenda-waarden: ronde getallen, grootste ≈ het maximum in de data
legend_vals = [500, 2000, int(round(nmax / 500) * 500)]
add_proportional_legend(ax, legend_vals, [v / nmax * S_MAX for v in legend_vals],
                        title="Aantal bomen", corner="auto",
                        facecolor=ASSET_COLORS["bomen"], edgecolor="#14512c", alpha=0.65)

for w in validate_map(fig, ax, data=per_buurt):
    print("WARN:", w)
save_map(fig, "bomen_per_buurt_proportioneel")
```

**Valkuilen**
- `s` **lineair** in de waarde houden. Schaal je de straal lineair, dan groeit het
  oppervlak kwadratisch en overdrijft de kaart grote waarden fors.
- **`S_MAX` afstemmen op de dichtheid van de vlakken.** Stadsbreed op TIR-buurt werkt
  ~600; op subbuurt lager. Te groot = onleesbare kluwen in de dichte buurten.
- **Nulwaarden overslaan** — een cirkel met oppervlak 0 rendert als ruis.
- `alpha` rond 0,65 met een donkere rand, zodat overlappende cirkels nog te scheiden zijn.
- Gebruik een **unieke** `key` (`TEKST`, de TIR-code) — buurtnamen zijn niet uniek
  (bv. "Dorp" komt meermaals voor).
- **Nul is geen afwezigheid.** Een gebied zonder objecten krijgt geen cirkel en is
  dan niet te onderscheiden van "buiten de data". Vul die vlakken lichtgrijs en zet
  de klasse in de legenda via `extras=` (invariant 4):

```python
GEEN = "#d9d9d9"
per_sb[per_sb["n"] == 0].plot(ax=ax, facecolor=GEEN, alpha=0.85,
                              edgecolor=STYLE["boundary_color"],
                              linewidth=0.25, zorder=2.5)
add_proportional_legend(ax, legend_vals, legend_sizes, title="Aantal bomen",
                        extras=[(GEEN, "Geen bomen")])   # kleurstaal onder de cirkels
```
