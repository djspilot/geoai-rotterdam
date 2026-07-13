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
