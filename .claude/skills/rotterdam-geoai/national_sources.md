# Dutch National Geo Sources (Beyond Rotterdam)

Most Rotterdam projects need context layers (buildings, addresses, height, basemaps, statistics) that are not in `diensten.rotterdam.nl`. These come from **PDOK** (Publieke Dienstverlening op de Kaart) and **CBS**. All listed here are free and require no API key.

## In dialoog: gebruik NL-GOV-MCP eerst

Voor conversational queries over nationale data: routeer via `nl_gov_ask` (NL-GOV-MCP, zie `mcp_notes.md`). Eén tool dekt 24 connectors met date-parsing en cross-source linking.

**Voorbeelden** (één MCP-call vervangt veel Python):
- *"Aantal sociale huurwoningen Rotterdam sinds 2020"* → `nl_gov_ask` → CBS + relevante connectors
- *"Luchtkwaliteit Rotterdam centrum vandaag"* → Luchtmeetnet-connector
- *"Bouwjaar pand Coolsingel 40"* → PDOK/BAG Individuele Bevragingen
- *"Rotterdamse raadsbesluiten over afvalbeleid 2025"* → ORI-connector
- *"Vigerend bestemmingsplan op deze coördinaat"* → Ruimtelijkeplannen-connector

De rauwe endpoints hieronder blijven canoniek voor: (a) batch-downloads in scripts, (b) bronnen die NL-GOV-MCP niet (of nog niet) dekt, (c) reproduceerbare pipelines met de `rotterdam` package.

## PDOK Locatieserver — Geocoding & Address Lookup

> **MCP**: `pdok__geocode` (standalone Locatieserver-MCP) of NL-GOV-MCP PDOK-connector. **Script**: `rotterdam.pdok_geocode_rd()`.

Best-in-class free Dutch geocoder. No key, no quota in practice.

- **Free-text search**: `https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=<query>&rows=10`
- **Suggest (autocomplete)**: `.../search/v3_1/suggest?q=<prefix>`
- **Lookup by id**: `.../search/v3_1/lookup?id=<id>&fl=*`
- **Reverse geocode (lon, lat in WGS84)**: `.../search/v3_1/reverse?lat=51.92&lon=4.48`

Returned `centroide_rd` is already in EPSG:28992 — use directly with Rotterdam data.

See `rotterdam.pdok_geocode("Coolsingel 40, Rotterdam")`.

## BAG — Buildings & Addresses

> **MCP**: NL-GOV-MCP PDOK/BAG-connector (incl. Kadaster Individuele Bevragingen voor oppervlakte/bouwjaar/gebruiksdoel per adres) of Kadaster BAG SPARQL-connector. **Script**: WFS/OGC API URL hieronder.

Basisregistratie Adressen en Gebouwen. Authoritative for every NL building polygon and address.

- **WFS**: `https://service.pdok.nl/lv/bag/wfs/v2_0?service=WFS&request=GetCapabilities`
- **WMS (rendered tiles)**: `https://service.pdok.nl/lv/bag/wms/v2_0`
- **OGC API Features**: `https://api.pdok.nl/lv/bag/ogc/v1/`
- Key feature types: `bag:pand` (building footprints), `bag:verblijfsobject`, `bag:ligplaats`, `bag:standplaats`.

## 3D BAG — Building Heights & LoD

3D building models with roof heights, ground heights, year of construction.

- **WFS**: `https://data.3dbag.nl/api/BAG3D/wfs?service=WFS&request=GetCapabilities`
- Useful properties: `h_dak_max`, `h_dak_min`, `h_maaiveld`, `b3_bouwjaar`.

## BGT — Large-Scale Base Map

Basisregistratie Grootschalige Topografie. Centimeter-precise topographic features (roads, water, vegetation, etc.).

- **WFS**: `https://service.pdok.nl/lv/bgt/wfs/v1_0?service=WFS&request=GetCapabilities`
- **WMTS (tiles)**: `https://service.pdok.nl/lv/bgt/wmts/v1_0`
- Heavy dataset — always filter by bbox.

## BRT — Topographic Map (Top10NL, TopRD)

- **WMTS basemap**: `https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0` (best static-map basemap for NL)
- Layers: `standaard`, `grijs`, `pastel`, `water`.

## Luchtfoto — Aerial Imagery

- **WMTS RGB (25 cm)**: `https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0`
- **WMTS Infrared**: `https://service.pdok.nl/hwh/luchtfotoir/wmts/v1_0`

## AHN — National Height Model (LiDAR)

Heights / DSM / DTM from airborne LiDAR. AHN5 is current as of 2026.

- **WMS**: `https://service.pdok.nl/rws/ahn/wms/v1_0`
- **WCS (raster downloads)**: `https://service.pdok.nl/rws/ahn/wcs/v1_0`
- Layers include `dsm_05m`, `dtm_05m` and gridded variants.

## CBS Wijk- en Buurtkaart (for normalization)

> **MCP**: `cbs_tables_search` + `cbs_observations` (NL-GOV-MCP, met trend-enrichment). **Script**: `rotterdam.cbs_buurten_rotterdam(year=2024)` voor polygons + inwoneraantal in één geopandas-frame.

Authoritative source for **population per buurt** — required for any honest choropleth. Updated yearly.

- **WFS**: `https://service.pdok.nl/cbs/wijkenbuurten/2024/wfs/v1_0?service=WFS&request=GetCapabilities`
- Key fields: `aantal_inwoners`, `oppervlakte_land_in_ha`, `gemiddelde_woz_waarde`.
- Join to Rotterdam TIR buurten on geometric overlap (CBS `buurtcode` does NOT map 1:1 to TIR `BUURT`).

## CBS Open Data (Statline)

> **MCP**: `cbs_tables_search` + `cbs_observations` (NL-GOV-MCP). Geen URL-bouwwerk meer nodig in dialoog.

For socio-economic indicators (income, household composition, age, etc.) at buurt level.

- **OData v4 root**: `https://opendata.cbs.nl/ODataApi/odata/`
- Discover tables: `https://opendata.cbs.nl/ODataApi/odata/` — every dataset has its own URL like `.../85618NED/TypedDataSet`.

## Rotterdam Open Data Portal

> **MCP**: NL-GOV-MCP `data_overheid_datasets_search` (data.overheid.nl, CKAN) — Rotterdam-datasets zitten in de nationale catalog. Filter op publisher of organisatie.

Catalog of Rotterdam-specific datasets beyond Obsurv/TIR.

- Portal: `https://rotterdamopendata.nl/`
- Includes traffic, energie, sociaal-economisch, evenementen, etc.

## OpenStreetMap (Overpass)

When you need POIs, paths, or features absent from BGT/Obsurv.

- **Overpass API**: `https://overpass-api.de/api/interpreter`
- Use `[out:json][bbox]` and a small Overpass-QL query — never download the planet.

## NDW — Traffic Data

> **MCP**: NL-GOV-MCP NDW-connector (discovery/metadata).

National Data Warehouse for traffic. Real-time traffic counts, incidents, parking.

- Open data portal: `https://opendata.ndw.nu/`
- Static feeds (XML/JSON): `https://opendata.ndw.nu/`

## Niet eerder genoemd — nu via NL-GOV-MCP wel binnen bereik

| Bron | NL-GOV-MCP-connector | Use case |
|---|---|---|
| **Luchtmeetnet** | live air quality measurements | Luchtkwaliteit per station / locatie in Rotterdam |
| **KNMI** | datasets/files, warnings, earthquakes (key vereist) | Weer-context bij stedelijke analyse |
| **ORI** (Open Raadsinformatie) | discovery | Rotterdamse raadsbesluiten / agenda's / moties |
| **Ruimtelijke plannen** (Wro/Bro) | via PDOK WMS, status- en gemeentefilter | Bestemmingsplan op coördinaat / in gebied |
| **Rijkswaterstaat** | water data catalog + real-time measurements | Waterstanden, scheepvaart |
| **Rechtspraak** | uitspraken.rechtspraak.nl backend | Jurisprudentie rond bv. ruimtelijke besluiten |
| **DSO Omgevingsdocumenten** | discovery (key vereist) | Omgevingsplannen/visies onder de Omgevingswet |
| **RIVM** | discovery | Publieke gezondheid |
| **NGR** | CSW metadata | Nationale geo-register catalog |
| **RCE Linked Data** | SPARQL | Cultureel erfgoed (monumenten) |

## Practical Recipes

**Pick basemap for a static matplotlib map**:

```python
import contextily as cx
# After plotting RD-projected layers on ax:
cx.add_basemap(ax, crs="EPSG:28992",
               source="https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0?"
                      "layer=grijs&style=default&tilematrixset=EPSG:28992"
                      "&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/png"
                      "&TileMatrix={z}&TileCol={x}&TileRow={y}")
```

**Normalize a Rotterdam choropleth by population**:

```python
import geopandas as gpd
cbs = gpd.read_file(
    "https://service.pdok.nl/cbs/wijkenbuurten/2024/wfs/v1_0"
    "?service=WFS&request=GetFeature&typeNames=wijkenbuurten:buurten"
    "&filter=<Filter><PropertyIsEqualTo><PropertyName>gemeentenaam</PropertyName>"
    "<Literal>Rotterdam</Literal></PropertyIsEqualTo></Filter>"
)
# Spatial join, then: density = count / cbs['aantal_inwoners'] * 1000
```

**Geocode an address**:

```python
from rotterdam import pdok_geocode
hits = pdok_geocode("Coolsingel 40, Rotterdam")
x, y = map(float, hits[0]["centroide_rd"].replace("POINT(", "").rstrip(")").split())
```
