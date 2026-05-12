---
name: rotterdam-geoai
description: Use when working with Rotterdam municipality GIS data, IMBOR 2025 asset management model, TIR territorial boundaries, Dutch public space (beheer openbare ruimte) datasets, or when asked to create maps/visualizations of Rotterdam assets. Triggers on Rotterdam geodata, WFS services, ArcGIS REST endpoints, IMBOR vocabulary, TIR gebieden/buurten, QGIS workflows, or questions like "toon op kaart", "maak een kaart", "where are the trees", "hoeveel per wijk".
---

# Rotterdam GeoAI

## Overview

Reference skill for working with **Gemeente Rotterdam** geodata services and the **IMBOR 2025** information model for public space asset management.

## Key Concepts

**IMBOR** (Informatiemodel Beheer Openbare Ruimte): Dutch CROW standard for recording/exchanging public space object data. Covers roads, greenery, lighting, waste containers, trees, sewers. Published as RDF/OWL Linked Data (`.ttl`) and Access database (`.accdb`).

**TIR** (Territoriale Indeling Rotterdam): Municipal territorial reference structure with levels: gemeente > gebied > buurt > subbuurt > subbuurtdeel.

TIR uses a **9-position coding system**: positions 1-3 = gemeentenummer (599 = Rotterdam), positions 4-5 = gebied, positions 6-7 = buurtnummer, position 8 = subbuurtnummer, position 9 = subbuurtdeelnummer. The bloknummer (positions 8-9 in a longer code) is NOT part of the TIR classification. CBS uses an 8-position system: positions 1-4 = gemeentecode, 5-6 = wijk, 7-8 = buurtnummer.

Example: `59905581403` → 599 (Rotterdam) + 05 (Gebied Noord) + 58 (Blijdorpsepolder) + 1 (subbuurt) + 4 (subbuurtdeel) + 03 (bloknummer, outside TIR).

**Obsurv**: The primary source system for Rotterdam asset management data. All asset layers (bomen, afvalbakken, lichtpunten, etc.) originate from Obsurv as managed by Gemeente Rotterdam.

## Data Sources

### TIR Layers (ArcGIS REST + WFS)

| Layer | REST URL | Index |
|-------|----------|-------|
| Gemeente | `https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/0` | 0 |
| Gebieden | `.../SB_BI/TIR/MapServer/1` | 1 |
| Buurten | `.../SB_BI/TIR/MapServer/2` | 2 |
| Subbuurten | `.../SB_BI/TIR/MapServer/3` | 3 |
| Subbuurtdelen | `.../SB_BI/TIR/MapServer/4` | 4 |

**WFS endpoint (ArcGIS)**: `https://diensten.rotterdam.nl/arcgis/services/SB_BI/TIR/MapServer/WFSServer?request=GetCapabilities&service=WFS`

**WFS endpoint (alternatief)**: `https://www.gis.rotterdam.nl/gisweb2/INTIR.COM/wfs?Service=WFS&Request=GetCapabilities`

### Asset Layers (folder: SB_Infra)

Base REST: `https://diensten.rotterdam.nl/arcgis/rest/services/`
Base WFS:  `https://diensten.rotterdam.nl/arcgis/services/`

| Asset | REST MapServer | WFS | JSON/pjson |
|-------|---------------|-----|------------|
| Bomen | `SB_Infra/Bomen/MapServer` | `SB_Infra/Bomen/MapServer/WFSServer?request=GetCapabilities&service=WFS` | `SB_Infra/Bomen/FeatureServer?f=pjson` |
| Afvalbakken | `SB_Infra/Afvalbak/MapServer` | `SB_Infra/Afvalbak/MapServer/WFSServer?request=GetCapabilities&service=WFS` | `SB_Infra/Afvalbak/MapServer?f=pjson` |
| Banken | `SB_Infra/Banken/MapServer` | `SB_Infra/Banken/MapServer/WFSServer?request=GetCapabilities&service=WFS` | `SB_Infra/Banken/MapServer?f=pjson` |
| Lichtpunten* | `SB_Infra/LICHTPUNTEN/MapServer` | `SB_Infra/LICHTPUNTEN/MapServer/WFSServer?request=GetCapabilities&service=WFS` | `SB_Infra/LICHTPUNTEN/MapServer?f=pjson` |
| Wegvakonderdelen | `SB_Infra/Wegvakonderdelen/MapServer` | `SB_Infra/Wegvakonderdelen/MapServer/WFSServer?request=GetCapabilities&service=WFS` | `SB_Infra/Wegvakonderdelen/MapServer?f=pjson` |
| Containers | `SB_Infra/Container/MapServer` | — | — |
| Lichtmasten | niet beschikbaar in service | — | — |

*Lichtpunten bevat zowel lantarenpalen (lichtmasten), grondspots, aanstraalverlichting, schijnwerpers, sierverlichting als wandarmaturen. Het type staat in het veld `LICHTPUNTTYPE`. **Let op**: in Lichtpunten verwijst het veld `WIJK` naar de TIR-buurt (bijv. "Stadsdriehoek") en `BUURT` naar de subbuurt (bijv. "Stadsdriehoek - 01"). Filter op `WIJK` om een heel TIR-buurt-niveau te selecteren.

### Access Formats

- **ArcGIS REST**: best for ESRI stack and scripting (supports `f=geojson`, `f=pjson`)
- **WFS (OGC)**: best for QGIS and open-standards GIS
- **pjson/JSON**: inspection, documentation, scripting

## Downloading Data via Python

Use ArcGIS REST query endpoints with pagination:

```python
# Key parameters for batch download
params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "outSR": "28992",          # RD New (Dutch national CRS)
    "resultOffset": str(offset),
    "resultRecordCount": str(batch_size),
    "f": "geojson",
}
url = f"{layer_url}/query?{urlencode(params)}"
```

- Default CRS: **EPSG:28992** (Amersfoort / RD New)
- Batch size: 1000 features per request
- Get total count first via `returnCountOnly=true`
- SSL verification may need to be relaxed for `diensten.rotterdam.nl`

## Loading in QGIS

### WFS layers
1. `Layer` > `Data Source Manager` > `WFS / OGC API - Features`
2. New connection > paste WFS GetCapabilities URL
3. Connect > select layers > Add

### PyQGIS script pattern
```python
uri = f"url='{endpoint}' typename='{typename}' version='2.0.0' srsname='EPSG:28992' restrictToRequestBBOX='1' pagingEnabled='true'"
layer = QgsVectorLayer(uri, title, "WFS")
QgsProject.instance().addMapLayer(layer, False)
group.addLayer(layer)
```

### Recommended workflow
1. Load TIR layers first (territorial reference)
2. Add asset WFS layers
3. Export to GeoPackage for local analysis
4. Use spatial joins (e.g., trees to neighborhoods)
5. Use IMBOR for field interpretation and domain values

## IMBOR 2025 Model Structure

The Linked Data package contains these ontology modules:

| Module | File | Purpose |
|--------|------|---------|
| Vocabulaire | `imbor2025-vocabulaire.ttl` | Terms and labels |
| Kern | `imbor2025-kern.ttl` | Core classes and properties |
| Domeinwaarden | `imbor2025-domeinwaarden.ttl` | Code lists / controlled values |
| Addendum geometrie | `imbor2025-addendum-geometrie.ttl` | Geometry constraints |
| Addendum materie | `imbor2025-addendum-materie.ttl` | Material concepts |
| Addendum OAGBD | `imbor2025-addendum-oagbd.ttl` | Lifecycle phases |
| Addendum referentiemodellen | `imbor2025-addendum-referentiemodellen.ttl` | External model links |
| MIM | `imbor2025-mim.ttl` | MIM mappings |

**Important**: `.ttl` files are RDF/OWL schema — NOT GIS vector layers. Load into triple store (GraphDB, Fuseki, Blazegraph) for SPARQL queries, or use as reference documentation.

SPARQL endpoints available — see `SPARQL-Endpoints.md` in the IMBOR package.

## Meetniveaus (Data Measurement Levels)

Understanding the measurement level of data determines the right visualization and statistical approach.

| Niveau | Type | Beschrijving | Voorbeelden |
|--------|------|-------------|-------------|
| **Nominaal** | Categorisch | Categorieën zonder volgorde | Type asset, buurtname, land |
| **Ordinaal** | Categorisch | Categorieën mét rangorde, geen meetbare afstanden | Tevredenheidsschaal, conditieklasse |
| **Interval** | Numeriek | Gelijke afstanden, geen absoluut nulpunt | Temperatuur (°C), jaartallen |
| **Ratio** | Numeriek | Gelijke afstanden + absoluut nulpunt | Lengte, gewicht, aantallen, oppervlakte |

**Rules for map/chart choices:**
- Nominaal/Ordinaal → categorical colors, no choropleth with raw counts
- Interval/Ratio → sequential or diverging color scales, arithmetic allowed
- Choropleth: **always normalize** ratio data (e.g. assets per km² or per 1000 inhabitants) — never show raw counts per area

## Generating Maps from Questions

When a user asks a question about Rotterdam assets or territories, generate a **static** map only.

### Decision: Which map type?

- **Exact locations, limited area, < ~5000 points** → point map
- **Many points or city-wide spread** → hexbin or very small scatter
- **Counts or values per area** → choropleth, but only with normalized values
- **Comparison between areas** → side-by-side static maps or static map + chart

#### Map Type Guide

| Data situation | Best map type |
|---------------|---------------|
| Point locations (< ~5000) | **Point map** — scatter |
| Point locations (> 5000) | **Dot density map** or **hexbin map** (avoid plotting all individually) |
| Count/value per area (normalized) | **Choropleth** — sequential palette |
| Deviation from a central value | **Choropleth** — diverging palette (e.g. ColorBrewer RdBu) |
| Proportional quantity per location | **Scaled symbol map** — circle area proportional to value |
| Two variables per area | **Bivariate choropleth** (or two side-by-side choropleths) |
| Point density / clustering | **Hexbin map** |
| Categorical distribution | **Dot map** with colors per category |

**Scaled symbol maps**: Use circle area (not radius) proportional to values. Can encode a second variable via color. Spikes (triangles) overlap less and tie better to exact locations.

**Dot density maps**: Each dot = one object (or N objects). Color encodes category. Use dasymetric masking to restrict dots to relevant areas.

**Hexbin maps**: Grid the map with hexagons, count points per hex. Scale hex size and/or color to encode one or two variables. Good for 10k+ points.

### Data Pipeline

Use local GeoJSON where available. Work in **EPSG:28992** for analysis and static cartography.

Before writing or running a map script, always do these preflight checks:

1. Confirm the required files actually exist under the project root.
2. Confirm the expected columns exist before filtering or joining.
3. Confirm the CRS is plausible for Rotterdam data.
4. Confirm output can be written to `output/`.
5. Inspect the candidate category field before mapping it.

Some Rotterdam GeoJSON files are mislabeled as `EPSG:4326` while their coordinates are clearly RD New. Use one compact loader everywhere instead of rewriting CRS logic per script:

```python
from pathlib import Path
import geopandas as gpd

PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "General data/Data"
OUT = PROJECT / "output"

def load_rotterdam(path):
    gdf = gpd.read_file(path)
    minx, miny, maxx, maxy = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)

def require_columns(gdf, columns, name):
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise KeyError(f"{name} mist kolommen: {missing}")

def require_paths(paths):
    missing = [str(path) for path in paths if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Ontbrekende databronnen: {missing}")
```

If data is not yet downloaded locally, fetch from ArcGIS REST first (see Download section above).

Before choosing a category field such as tree type, mast type, or asset type, inspect the actual value distribution first:

```python
for col in ["BOOMSORTIMENT_NEDERLANDS", "LICHTPUNTTYPE", "MASTTYPE", "TYPE"]:
    if col in gdf.columns:
        print(col)
        print(gdf[col].fillna("Onbekend").astype(str).value_counts().head(10).to_string())
        print()
```

Choose the field that is both semantically correct and readable on a legend.

### Local Data Files

Local data lives under `General data/Data/` relative to the project root (`/Users/ds/Werk/GEOAI test/`).

| File | Content | Geometry | Key Properties |
|------|---------|----------|----------------|
| `General data/Data/tir_gemeente.geojson` | Rotterdam boundary | Polygon | TEKST |
| `General data/Data/tir_gebieden.geojson` | 21 gebieden | Polygon | GEBDNAAM, GEBIED |
| `General data/Data/tir_buurten.geojson` | 91 buurten | Polygon | BUURTNAAM, GEBDNAAM, BUURT |
| `General data/Data/tir_subbuurten.geojson` | Subbuurten | Polygon | — |
| `General data/Data/tir_subbuurtdelen.geojson` | Subbuurtdelen | Polygon | — |
| `General data/Data/afvalbak.geojson` | 9743 afvalbakken | Point | TYPE, WIJK, STRAAT, WOONPLAATS |
| `General data/Data/bomen_chunks/*.geojson` | 199.487 bomen (100 chunks) | Point | Load all with `glob` |
| `General data/Data/lichtpunten_stadsdriehoek.geojson` | 3.493 lichtpunten (Stadsdriehoek) | Point | LICHTPUNTTYPE, MASTTYPE, WIJK, BUURT, STRAAT |

Context docs: `General data/context/Context.md`, `General data/context/Databronnen-WFS.md`, `General data/context/QGIS-Guide.md`

### Rotterdam Static Defaults

- **CRS**: `EPSG:28992` for analysis and final static maps
- **Reference center (Rotterdam centrum, RD New)**: `(92537, 437503)`
- **City overview figure size**: `figsize=(12, 10)` or `figsize=(14, 12)`
- **Gebied / buurt figure size**: `figsize=(10, 10)` or `figsize=(12, 12)`
- **Point marker size**: `0.3-1` for citywide dense layers, `2-6` for gebied/buurt maps
- **Boundary linewidth**: `0.4-0.8` for buurten, `0.8-1.2` for gebieden
- **Default polygon fill**: light neutral, e.g. `#f6f3ee`
- **Default boundary color**: muted dark neutral, e.g. `#8c8377` or `#666666`
- **Default point color**: one strong accent per asset layer, e.g. afval `#d94841`, bomen `#2d8a4e`, lichtpunten `#f2a900`
- **Label style**: dark text with thin white halo for busy backgrounds
- **Output**: save to `output/` as `PNG`; use `SVG` only when the user asks for publication-grade vector output

### Colour Defaults

- Use **contrasting colours** for different object types; avoid low-contrast gray-on-gray maps.
- For **sequential choropleths**, prefer ColorBrewer-style palettes such as `YlOrRd`, `OrRd`, `YlGn`, `Blues`.
- For **diverging choropleths**, prefer `RdBu`, `BrBG`, or `PuOr` around a meaningful midpoint.
- For **categorical maps**, keep the number of hues limited and clearly distinct.
- Use a **light neutral background** for administrative polygons so point layers stay visually dominant.
- Avoid saturated fills on both polygons and points at the same time; keep one quiet and one dominant.
- For dense point maps, reduce clutter with **smaller markers and alpha** before introducing extra colours.
- Prefer palettes and symbol choices that remain readable when exported to PNG and viewed in reports or slides.

### Workflow and Examples

When a user asks for a map, generate a **static** map only: `matplotlib + geopandas` to `PNG` or `SVG`.

Do not use Folium or HTML output unless the user explicitly overrides this rule.

For matplotlib scripts, prefer a headless-safe setup:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

### Decision: Which static map type?

- **Exact locations, limited area, < ~5000 points** → point map
- **Many points or city-wide spread** → hexbin or very small scatter with low alpha
- **Value per area** → choropleth, but only with normalized values
- **Comparison between areas** → side-by-side static maps or one choropleth plus a bar chart
- **Two dense point layers together** → prefer two panels over stacking both in one map
- **Many category values in one layer** → map top categories and aggregate the rest as `Overige typen`

### Standard Area Definitions

If the user asks for Rotterdam Zuid or Rotterdam Noord without further qualification, use explicit TIR gebied lists instead of inferring them ad hoc.

```python
ROTTERDAM_ZUID_GEBIEDEN = [
    "Feijenoord",
    "IJsselmonde",
    "Charlois",
    "Hoogvliet",
    "Pernis",
    "Rozenburg",
    "Waalhaven-Eemhaven",
    "Vondelingenplaat",
]

ROTTERDAM_NOORD_GEBIEDEN = [
    "Delfshaven",
    "Hillegersberg-Schiebroek",
    "Kralingen-Crooswijk",
    "Nieuw Mathenesse",
    "Noord",
    "Overschie",
    "Prins Alexander",
    "Rivium",
    "Rotterdam Centrum",
    "Rotterdam-Noord-West",
    "Spaanse Polder",
]
```

Always state this area definition briefly in the script output or caption when using it.

If a local dataset covers only part of the requested area, do not silently pretend it is complete. State the actual coverage in the title or caption, for example `Stadsdriehoek (deel van Rotterdam Centrum)`.

### Compact Python Template

Prefer this compact skeleton and adapt it, instead of retyping full scripts from scratch:

```python
from pathlib import Path
import geopandas as gpd
import matplotlib
import matplotlib.patheffects as pe
import pandas as pd
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "General data/Data"
OUT = PROJECT / "output"

def load_rotterdam(path):
    gdf = gpd.read_file(path)
    minx, miny, maxx, maxy = gdf.total_bounds
    if minx > 10_000 and miny > 300_000:
        return gdf.set_crs(epsg=28992, allow_override=True)
    if gdf.crs is None:
        return gdf.set_crs(epsg=28992)
    return gdf if gdf.crs.to_epsg() == 28992 else gdf.to_crs(epsg=28992)

def require_columns(gdf, columns, name):
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise KeyError(f"{name} mist kolommen: {missing}")

def require_paths(paths):
    missing = [str(path) for path in paths if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Ontbrekende databronnen: {missing}")

def top_n_with_other(series, n=8, other_label="Overige typen"):
    counts = series.fillna("Onbekend").astype(str).value_counts()
    top = counts.head(n).index.tolist()
    grouped = series.fillna("Onbekend").astype(str).where(lambda s: s.isin(top), other_label)
    return grouped, counts, top

def spatial_filter(points, areas, keep):
    subset = areas[areas[keep[0]].isin(keep[1])].copy()
    subset["geometry"] = subset.geometry.make_valid()
    return gpd.sjoin(points, subset, how="inner", predicate="within"), subset

def save_static(fig, name):
    OUT.mkdir(exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path
```

### Pattern: Point Map

```python
require_paths([DATA / "tir_gebieden.geojson", DATA / "afvalbak.geojson"])
gebieden = load_rotterdam(DATA / "tir_gebieden.geojson")
afval = load_rotterdam(DATA / "afvalbak.geojson")
require_columns(gebieden, ["GEBDNAAM", "geometry"], "tir_gebieden")
require_columns(afval, ["TYPE", "geometry"], "afvalbak")
afval_zuid, zuid = spatial_filter(
    afval,
    gebieden,
    ("GEBDNAAM", ROTTERDAM_ZUID_GEBIEDEN),
)

fig, ax = plt.subplots(figsize=(12, 12))
zuid.plot(ax=ax, color="#f6f3ee", edgecolor="#8c8377", linewidth=0.8)
afval_zuid.plot(ax=ax, color="#d94841", markersize=3, alpha=0.75)
ax.set_title("Afvalbakken in Rotterdam Zuid", fontsize=16, fontweight="bold")
ax.set_axis_off()
save_static(fig, "afvalbakken_rotterdam_zuid.png")
```

### Pattern: Choropleth

```python
require_paths([DATA / "tir_buurten.geojson", DATA / "afvalbak.geojson"])
buurten = load_rotterdam(DATA / "tir_buurten.geojson")
afval = load_rotterdam(DATA / "afvalbak.geojson")
require_columns(buurten, ["BUURTNAAM", "geometry"], "tir_buurten")
joined = gpd.sjoin(afval, buurten, how="inner", predicate="within")
counts = joined.groupby("BUURTNAAM").size().rename("count")
buurten = buurten.join(counts, on="BUURTNAAM").fillna({"count": 0})
buurten["area_km2"] = buurten.geometry.area / 1_000_000
buurten["count_per_km2"] = buurten["count"] / buurten["area_km2"]

fig, ax = plt.subplots(figsize=(12, 10))
buurten.plot(
    column="count_per_km2",
    cmap="YlOrRd",
    linewidth=0.4,
    edgecolor="#666666",
    legend=True,
    ax=ax,
)
ax.set_title("Afvalbakken per km² per buurt", fontsize=16, fontweight="bold")
ax.set_axis_off()
save_static(fig, "afvalbakken_per_km2_buurt.png")
```

### Pattern: Load Chunked Bomen Data

```python
from glob import glob

chunk_paths = sorted(glob(str(DATA / "bomen_chunks/*.geojson")))
if not chunk_paths:
    raise FileNotFoundError("Geen bomen-chunks gevonden in data map")
bomen = pd.concat([gpd.read_file(path) for path in chunk_paths], ignore_index=True)
bomen = gpd.GeoDataFrame(bomen, geometry="geometry", crs="EPSG:28992")
```

### Token-Efficient Python Rules

- Reuse `DATA`, `OUT`, `load_rotterdam`, `spatial_filter`, and `save_static` instead of rewriting path, CRS, and save logic.
- Always reuse `PROJECT`, `require_paths`, and `require_columns` instead of repeating ad hoc checks.
- For categorical splits, inspect field distributions first and then use `top_n_with_other()` instead of dumping dozens of legend classes.
- Prefer one compact helper over repeated defensive CRS snippets.
- Prefer `groupby(...).size().rename(...)` over multi-step dataframe reshaping when a single count column is enough.
- Keep plotting code to one background layer, one data layer, one title block, one save call.
- Only add label loops when labels materially improve readability.
- If the same pattern appears for multiple assets, write one parameterized function instead of duplicating a script body.
- For recurring downloads or joins, prefer creating a bundled script in the skill instead of re-emitting long code in the conversation.
- If two dense point layers compete visually, switch to a two-panel layout before adding more legend complexity.
- Prefer `fig.subplots_adjust(...)` when `tight_layout()` produces warnings or clipped legends.

### Kartografische Richtlijnen (Required for every map)

These rules apply to all maps — always follow them:

1. **Titel**: Altijd bovenaan. Bevat onderwerp + locatie (indien bekend) + periode (indien bekend).
2. **Legenda**: Altijd opnemen. Alle afgebeelde kaartobjecten moeten erin staan. Ontbrekende waarden labelen als `"Waarde onbekend"`.
3. **Schaalstok**: Altijd toevoegen. Afstanden weergeven in afgeronde gehele getallen (metrisch: m of km).
4. **Projectie**: Kaarten over Nederland altijd in **EPSG:28992** (Amersfoort / RD New). Niet Mercator.
5. **Laagvolgorde**: Puntsymbolen > Lijnen > Vlakken (punten altijd bovenaan).
6. **Labels**: Gebruik een dunne witte halo op labels als de achtergrond veel kleuren heeft (bijv. luchtfoto).
7. **Kleuren**: Contrasterende kleuren voor verschillende objecttypes.
8. **Classificatie kwantitatieve data**: Max 5 klassen (absoluut max 9). Klassegrenzen afgerond op ronde getallen (behalve min en max).
9. **Choropleet normalisatie**: **Altijd normaliseren** op inwonertal of gebiedsoppervlakte. Nooit ruwe aantallen per gebied.
10. **Kleurpaletten**: Sequentieel voor oplopende waarden; divergerend voor afwijkingen van een centrale waarde. Gebruik ColorBrewer als referentie.

**Cartography reference**: Geo-visualisatie Deel B (geo-visualisatie) en Deel C (kaartopmaak) op Wikibooks.

### Answering Questions with Maps

When the user asks a question, determine:

1. **What data is needed?** → load the smallest relevant local layer(s)
2. **Do the files and required columns exist?** → fail fast if not
3. **Is the question about location or comparison?** → choose point map vs choropleth
4. **What is the scope?** → city, gebied, buurt, subbuurt
5. **Are there too many points for one readable panel?** → switch to hexbin or two panels
6. **Are there too many categories for a readable legend?** → use top N + `Overige typen`
7. **Can the code reuse the compact helpers above?** → if yes, do that instead of writing a fresh script

Examples:

| Question | Action |
|----------|--------|
| "Waar staan de afvalbakken in Kralingen?" | Static point map |
| "Hoeveel bomen per wijk?" | Static choropleth with normalization |
| "Toon alle gebieden van Rotterdam" | Static polygon map |
| "Welke buurt heeft de meeste banken?" | Spatial join + bar chart + highlighted static map |
| "Vergelijk afvalbakken noord vs zuid" | Two static maps or one normalized comparison chart |

## Common Mistakes

- **CRS mismatch in Rotterdam GeoJSON**: Some files carry `EPSG:4326` metadata while coordinates are actually RD New. Use `load_rotterdam()`, not a naive `set_crs()` or blind `to_crs()`.
- **Relative path fragility**: Scripts that assume the shell cwd matches the project root will fail unpredictably. Build paths from `Path(__file__).resolve().parent`.
- **Wrong category field**: Some datasets have multiple plausible type columns. Inspect value distributions before choosing what to map.
- **Empty geometries**: TIR layers can contain features with null or empty geometries. Always guard before computing centroids or coordinates:
  ```python
  for _, row in gdf.iterrows():
      if row.geometry is None or row.geometry.is_empty:
          continue
      centroid = row.geometry.centroid
      if centroid.is_empty:
          continue
      # safe to use centroid.x, centroid.y
  ```
- **Deprecated matplotlib `get_cmap`**: `plt.cm.get_cmap("YlOrRd", n)` is deprecated since matplotlib 3.7. Use `plt.colormaps.get_cmap("YlOrRd").resampled(n)` instead.
- **WIJK vs BUURT veldnamen in asset layers**: In sommige asset layers (bijv. Lichtpunten, Afvalbakken) verwijst `WIJK` naar het TIR-buurtniveau en `BUURT` naar het sub-buurtniveau. Dit is verwarrend: filter op `WIJK` als je een TIR-buurt wilt selecteren (bijv. `WIJK='Stadsdriehoek'`), niet op `BUURT`.
- Trying to open `.ttl` files as GIS layers — they are semantic model files
- Using only WFS when ArcGIS REST query is more reliable for bulk downloads
- Forgetting to set `outSR=28992` (Dutch RD New coordinate system)
- Not paginating large layers (bomen has 100k+ features)
- Treating IMBOR as a spatial dataset instead of as a schema reference
- **Choropleth without normalization**: showing raw counts per buurt/gebied is misleading — always divide by population or area (e.g. assets per km² or per 1000 inhabitants)
- **Too many classes in choropleth**: using more than 5-9 classes makes maps unreadable — prefer 5, max 9
- **Wrong map projection**: using Mercator/WGS84 for NL static maps — always use EPSG:28992 for matplotlib/geopandas maps over the Netherlands
- **Missing map elements**: forgetting title, legend, or scale bar — all three are required for every map
- Writing long one-off Python snippets when the same task can be expressed with the compact helpers above
- Stacking two dense point layers on one map when a two-panel layout would be clearer
- Skipping preflight file or column validation and discovering the problem only at render time
- Using every unique category value directly in the legend instead of top N + `Overige typen`
- Presenting a partial local extract as if it covered the full requested Rotterdam area
