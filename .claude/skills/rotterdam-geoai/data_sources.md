# Rotterdam Data Sources (TIR + Assets via Obsurv)

For PDOK/CBS/AHN national sources see **`national_sources.md`**.

## Local files (canonical for this project)

Loaded with `rotterdam.load_layer(name)` — handles CRS quirks. Paths in `rotterdam.LOCAL_FILES`.

| Layer key | File | Records | Geom | Key fields |
|-----------|------|---------|------|-----------|
| `gemeente` | `tir_gemeente.geojson` | 1 | Polygon | TEKST |
| `gebieden` | `tir_gebieden.geojson` | 21 | Polygon | GEBDNAAM, GEBIED |
| `buurten` | `tir_buurten.geojson` | 91 | Polygon | BUURTNAAM, GEBDNAAM, BUURT |
| `subbuurten` | `tir_subbuurten.geojson` | — | Polygon | — |
| `subbuurtdelen` | `tir_subbuurtdelen.geojson` | — | Polygon | — |
| `afvalbak` | `afvalbak.geojson` | 9743 | Point | TYPE, WIJK, STRAAT, WOONPLAATS |
| `bomen` | `bomen_chunks/*.geojson` | 199 487 | Point | (load via `load_layer("bomen")`) |
| `lichtpunten_stadsdriehoek` | `lichtpunten_stadsdriehoek.geojson` | 3 493 | Point | LICHTPUNTTYPE, MASTTYPE, WIJK, BUURT |

Context: `General data/context/Context.md`, `Databronnen-WFS.md`, `QGIS-Guide.md`.

## Field-name gotcha (asset layers)

In Lichtpunten/Afvalbakken/Bomen verwijst:

- `WIJK` → **TIR-buurt** (bijv. "Stadsdriehoek")
- `BUURT` → **TIR-subbuurt** (bijv. "Stadsdriehoek - 01")

Filter altijd op `WIJK` als de gebruiker "buurt" zegt op TIR-niveau. Zie `rotterdam.ASSET_BUURT_FIELD`.

## ArcGIS REST endpoints (live download)

Base: `https://diensten.rotterdam.nl/arcgis/rest/services/`. Mapping in `rotterdam.ARCGIS_LAYERS`. Use `rotterdam.fetch_arcgis_layer(url)` voor gepagineerde download.

### TIR (folder: SB_BI)

| Layer | Path |
|-------|------|
| Gemeente / Gebieden / Buurten / Subbuurten / Subbuurtdelen | `SB_BI/TIR/MapServer/{0..4}` |

WFS-variant: `https://diensten.rotterdam.nl/arcgis/services/SB_BI/TIR/MapServer/WFSServer?request=GetCapabilities&service=WFS`

Alt WFS: `https://www.gis.rotterdam.nl/gisweb2/INTIR.COM/wfs?Service=WFS&Request=GetCapabilities`

### Assets (folder: SB_Infra)

| Asset | MapServer |
|-------|-----------|
| Bomen | `SB_Infra/Bomen/MapServer` |
| Afvalbakken | `SB_Infra/Afvalbak/MapServer` |
| Banken | `SB_Infra/Banken/MapServer` |
| Lichtpunten | `SB_Infra/LICHTPUNTEN/MapServer` |
| Wegvakonderdelen | `SB_Infra/Wegvakonderdelen/MapServer` |
| Containers | `SB_Infra/Container/MapServer` |

Voor WFS: vervang `rest/services` door `services` en plak `WFSServer?request=GetCapabilities&service=WFS` aan het pad.

Voor JSON metadata: voeg `?f=pjson` toe.

**Lichtpunten** bevat lantarenpalen, grondspots, aanstraalverlichting, schijnwerpers, sierverlichting en wandarmaturen. Veld `LICHTPUNTTYPE` onderscheidt ze.

## Toegangsformaten — wanneer welk

- **ArcGIS REST** (`f=geojson`/`f=pjson`) → bulk-download via Python, scripting.
- **WFS** (OGC) → QGIS en open standaarden.
- **pjson** → inspectie van schema en domeinwaarden.

## Standaard gebiedsindelingen

Wanneer de gebruiker "Rotterdam Zuid" of "Rotterdam Noord" zegt zonder verdere afbakening, gebruik:

- `rotterdam.ROTTERDAM_ZUID_GEBIEDEN` (8 gebieden inclusief Hoogvliet, Pernis, Rozenburg, Waalhaven-Eemhaven, Vondelingenplaat)
- `rotterdam.ROTTERDAM_NOORD_GEBIEDEN` (11 gebieden)

Vermeld de definitie altijd kort in caption of script-output.

Voor strikte attribuutfilters op asset layers gebruik twee stappen:

1. Attribuutfilter op `WOONPLAATS IN (...)` voor snelle download.
2. Ruimtelijke verificatie via `filter_to_area(assets, gebieden, gebied_names=ROTTERDAM_ZUID_GEBIEDEN)`.

Rapporteer beide counts — afwijking duidt op vervuiling in `WOONPLAATS`.

## IMBOR — niet ruimtelijk

`.ttl` bestanden van **IMBOR 2025** zijn RDF/OWL schemas, géén vectorlagen. Laden in GraphDB/Fuseki/Blazegraph voor SPARQL, of behandelen als referentiedocumentatie voor veldbetekenis en domeinwaarden.

Modules: `vocabulaire`, `kern`, `domeinwaarden`, `addendum-geometrie`, `addendum-materie`, `addendum-oagbd`, `addendum-referentiemodellen`, `mim`.
