---
name: rotterdam-geoai
description: Use when working with Rotterdam municipality GIS data, IMBOR 2025 asset management model, TIR territorial boundaries, Dutch public space (beheer openbare ruimte) datasets, or when asked to create maps/visualizations of Rotterdam assets. Triggers on Rotterdam geodata, WFS services, ArcGIS REST endpoints, IMBOR vocabulary, TIR gebieden/buurten, QGIS workflows, or questions like "toon op kaart", "maak een kaart", "where are the trees", "hoeveel per wijk".
---

# Rotterdam GeoAI

End-to-end skill voor het beantwoorden van GIS-vragen over Rotterdam: data ophalen, opschonen, koppelen aan TIR / CBS, en publiceren als kaart volgens de Rotterdamse kartografische richtlijnen.

## Quickstart

De canonieke library woont in het project zelf, niet in de skill:

```
/Users/ds/Werk/GEOAI test/General data/rotterdam/
```

```python
import sys
sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")
from rotterdam import (
    load_layer, filter_to_area, point_map, finalize_map, save_map,
    ROTTERDAM_ZUID_GEBIEDEN,
)

gebieden = load_layer("gebieden")
afval    = load_layer("afvalbak")
zuid     = filter_to_area(afval, gebieden, gebied_names=ROTTERDAM_ZUID_GEBIEDEN)
fig, ax  = point_map(zuid,
                     boundary=gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_ZUID_GEBIEDEN)],
                     title="Afvalbakken in Rotterdam Zuid")
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl")
save_map(fig, "afvalbakken_rotterdam_zuid")   # → output/maps/...
```

Een typisch script is 10–20 regels. Het zware werk zit in de `rotterdam`-package.

> **Back-compat**: `from helpers import ...` (skill-pad) blijft werken; `helpers.py` is nu een shim die alles uit `rotterdam` herexporteert. Nieuwe scripts: importeer direct uit `rotterdam`.

## Wanneer welk bestand laden

| Vraag van de gebruiker | Lees |
|------------------------|------|
| Welke functies / constanten zijn er? | `rotterdam/__init__.py` (publieke API) of submodule |
| Welke kaartelementen, kleuren, klassen? | **`cartography.md`** + `rotterdam/cartography.py` |
| Welke Rotterdamse endpoints + lokale files? | **`data_sources.md`** + `rotterdam/vocab.py` |
| Adres opzoeken, BAG, AHN, CBS, basemap? | **`national_sources.md`** + `rotterdam/geocode.py` |
| Nationale data in dialoog (CBS, KNMI, Luchtmeetnet, ORI raadsbesluiten, Ruimtelijke plannen, Tweede Kamer, Rechtspraak, …) | **`mcp_notes.md`** — NL-GOV-MCP `nl_gov_ask` |
| Hoe maak ik X? (kant-en-klare snippets) | **`patterns.md`** |
| "Waarom werkt mijn script niet?" | **`troubleshooting.md`** |
| Bestaat er een MCP voor? | **`mcp_notes.md`** |

## Kernconcepten (memoriseren — niet doorklikken)

- **TIR** = Territoriale Indeling Rotterdam: `gemeente > gebied > buurt > subbuurt > subbuurtdeel`. 9-positie code: 599 (Rotterdam) + 2 (gebied) + 2 (buurt) + 1 (subbuurt) + 1 (subbuurtdeel). Bloknummer hoort niet bij TIR. CBS gebruikt een 8-positie systeem en mapt niet 1:1 op TIR.
- **Obsurv** = bronsysteem voor alle asset-data (bomen, afvalbakken, lichtpunten, banken, containers, wegvakonderdelen).
- **IMBOR 2025** = CROW-standaard schema voor objectbetekenis. `.ttl`-bestanden zijn RDF/OWL, géén vectorlagen.
- **EPSG:28992** (Amersfoort / RD New) is dé werk-CRS. Folium krijgt WGS84.

## Harde invarianten

1. **CRS**: werk in EPSG:28992. Reproject pas naar WGS84 wanneer Folium het vraagt. Sommige Rotterdamse files claimen WGS84 maar bevatten RD-coordinaten — gebruik altijd `load_rotterdam()` / `load_layer()` uit `rotterdam.loader`.
2. **Asset-veldnamen**: in Lichtpunten, Afvalbakken e.a. is `WIJK` = TIR-buurt en `BUURT` = TIR-subbuurt. Filter op `WIJK` voor buurt-niveau.
3. **Choropleet altijd normaliseren** (per 1000 inwoners of per km²) — nooit ruwe counts per gebied. `count_per_polygon(..., normalize_by="aantal_inwoners")`.
4. **Kaart heeft altijd** titel, legenda, schaalstok, projectie. `style_map(ax, title)` regelt dit.
5. **Default output**: statische PNG via `save_map()`. Folium pas op expliciet verzoek.
6. **Rotterdam Zuid/Noord**: gebruik `ROTTERDAM_ZUID_GEBIEDEN` / `ROTTERDAM_NOORD_GEBIEDEN`. Vermeld de definitie in caption of script-output.

## Beslisboom: van vraag naar kaart

1. **Wat is gevraagd?** locaties tonen / vergelijken / verdeling / dichtheid / relatie tot ander attribuut.
2. **Welke data?** Eerst `LOCAL_FILES` (snel). Anders `fetch_arcgis_layer(ARCGIS_LAYERS[...])`. Voor inwoneraantallen → `cbs_buurten_rotterdam()`. Voor adressen → `pdok_geocode_rd()`.
3. **Welk gebied?** Stad → centroid Rotterdam, figsize (12,10). Gebied/buurt → `filter_to_area()`, figsize (10,10).
4. **Welk kaarttype?** Zie `cartography.md` map-type-tabel. Standaard: `point_map()` voor punten, `choropleth()` voor verhoudingen per gebied.
5. **Genormaliseerd?** Voor choropleet ja, altijd. `count_per_polygon(normalize_by=...)`.
6. **Polish**: `finalize_map(fig, source=..., date=..., suptitle=...)` — footer + marges + optionele paginatitel.
7. **Valideren**: `validate_map(fig, ax, data=..., normalized=True)`. Print warnings; fix vóór save.
8. **Output** naar `output/` via `save_map()`.

Twee complete vraag→antwoord flows staan in `patterns.md` (operationele vraag + briefkaart wethouder).

## Bundle-overzicht

Skill (alleen documentatie + back-compat shim):
```
~/.claude/skills/rotterdam-geoai/
├── SKILL.md             ← deze file: orchestratie + invarianten
├── helpers.py           ← shim die `rotterdam` package re-exporteert
├── cartography.md       ← richtlijnen + meetniveaus + map-type beslisboom
├── data_sources.md      ← Rotterdam endpoints + lokale files + IMBOR
├── national_sources.md  ← PDOK, BAG, 3D BAG, AHN, BRT basemap, CBS, OSM
├── patterns.md          ← runnable snippets per kaarttype
├── troubleshooting.md   ← veelgemaakte fouten
└── mcp_notes.md         ← status geo MCPs + bouwsuggesties
```

Project (canonieke library):
```
/Users/ds/Werk/GEOAI test/General data/rotterdam/
├── __init__.py     ← flat public API (re-exports)
├── paths.py        ← PROJECT_ROOT, DATA, OUTPUT, MAPS_DIR, CACHE
├── vocab.py        ← TIR-gebieden, ASSET_COLORS, LOCAL_FILES, ARCGIS_LAYERS, STYLE
├── loader.py       ← load_rotterdam, load_layer, require_columns/paths
├── tir.py          ← filter_to_area, count_per_polygon
├── cartography.py  ← point_map, choropleth, style_map, finalize_map, save_map, validate_map
├── arcgis.py       ← fetch_arcgis_layer (paginated REST + SSL workaround)
└── geocode.py      ← pdok_geocode_rd, cbs_buurten_rotterdam
```

## Publieke API — `from rotterdam import ...`

Per submodule (alles ook flat geherexporteerd via `rotterdam.__init__`):

**`rotterdam.paths`** — `PROJECT_ROOT`, `GENERAL_DATA`, `DATA`, `OUTPUT`, `MAPS_DIR`, `DATA_OUT`, `REPORTS_DIR`, `SCRIPTS_DIR`, `CACHE`. (Geen `Path(__file__).resolve().parents[N]` meer per script.)

**`rotterdam.vocab`** — `RD_NEW`, `WGS84`, `ROTTERDAM_CENTER_RD/WGS`, `ROTTERDAM_ZUID_GEBIEDEN`, `ROTTERDAM_NOORD_GEBIEDEN`, `ASSET_COLORS`, `LOCAL_FILES`, `ARCGIS_LAYERS`, `ASSET_BUURT_FIELD` (=`WIJK`), `ASSET_SUBBUURT_FIELD` (=`BUURT`), `STYLE`.

**`rotterdam.loader`** — `load_rotterdam(path)` (CRS-veilig), `load_layer(name)` (zie `LOCAL_FILES`), `require_columns`, `require_paths`, `safe_centroids`.

**`rotterdam.tir`** — `filter_to_area(assets, gebieden, gebied_names=...|buurt_names=..., buurten=...)`, `count_per_polygon(points, polys, key=..., normalize_by=..., per=1000)`.

**`rotterdam.cartography`** — `point_map`, `choropleth` → `(fig, ax)`. Pipeline: `point_map`/`choropleth` → `finalize_map(fig, source=..., date=...)` → `validate_map(fig, ax, data=...)` → `save_map(fig, "naam")` (default → `output/maps/naam.png`). Building blocks: `style_map`, `add_scalebar`, `add_north_arrow`, `add_pdok_basemap`, `setup_headless_matplotlib`.

**`rotterdam.arcgis`** — `fetch_arcgis_layer(url, where=..., out_sr=28992, batch_size=1000)` — paginated GeoJSON download. SSL workaround voor diensten.rotterdam.nl is ingebouwd.

**`rotterdam.geocode`** — `pdok_geocode(query)`, `pdok_geocode_rd(query) -> (x, y) | None`, `cbs_buurten_rotterdam(year=2024)`.

## MCPs — wanneer welke

Twee actieve geo-MCPs (volledig overzicht + routing-tabel in `mcp_notes.md`):

| MCP | Primair voor |
|---|---|
| `pdok` (lokaal gebouwd, Locatieserver) | Snelle adres/coord-lookups in dialoog |
| `nl-gov` ([WAINUTAI/NL-GOV-MCP](https://github.com/WAINUTAI/NL-GOV-MCP), 24 connectors / 52 tools) | Alle overige nationale data — CBS, BAG-detail, Ruimtelijke plannen, Luchtmeetnet, KNMI, ORI raadsbesluiten, Rechtspraak, Tweede Kamer, data.overheid.nl catalog, NDW, RWS, RDW etc. Topvragen via `nl_gov_ask`. |

**Vuistregel scripts vs dialoog**:
- **Script / batch / reproduceerbaar** → `from rotterdam import ...` (eigen package). Cartografie-pipeline blijft volledig Python.
- **Dialoog / eenmalige lookup** → MCP-tool. `pdok__*` voor geocoding, `nl_gov_ask` voor alles wat nationale data raakt.

Wat MCPs **niet** doen voor jou: Rotterdam-specifieke Obsurv-assets (afval/bomen/lichtpunten), TIR-gebieden, IMBOR-vocabulaire, kaart-rendering. Dat blijft `rotterdam` package.
