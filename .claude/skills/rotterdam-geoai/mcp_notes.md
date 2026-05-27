# Geo MCP Servers — Status & Usage

## Routing — welke vraag, welk gereedschap

Geverifieerd via live calls 2026-05-26. Kies **directe tool** boven `nl_gov_ask` als je weet welke bron je wil — de router is naïef bij domein-specifieke intent (zie "Bekende beperkingen").

| Vraag-type | Tool | Notitie |
|---|---|---|
| Adres → coord / coord → adres in dialoog | `pdok__geocode` / `pdok__reverse_geocode_rd` (standalone) of `mcp__nl-gov__pdok_search` | Snel, geen router-overhead. Standalone-MCP geeft RD én WGS in één call. |
| Adres in batch / script | `rotterdam.pdok_geocode_rd()` | Reproduceerbaar, deel van pipeline |
| BAG-detail per adres (oppervlakte, bouwjaar, gebruiksdoel) | `bag_address_detail(query=..., resolve_pand=True, …)` | Kan `null` returnen voor sommige verblijfsobjecten — niet elk pand heeft authoritative waarden in lookup_only mode |
| BAG-adres lookup (basisvelden) | `bag_lookup_address(query/postcode/huisnummer)` | Lichter dan `bag_address_detail` |
| Open exploratie — "welke NL-data is er over X?" | `nl_gov_ask` | Alléén voor catalog-discovery, niet voor domain-routing (gaat vaak naar data.overheid catalog) |
| CBS-tabel vinden | `cbs_tables_search(query)` | Keyword-fuzzy; specificeer in query (bv. "wijken buurten gemeente" ipv "wijken buurten 2024") |
| CBS-observaties ophalen | `cbs_observations(tableId, filters={...})` | Eerst tableId via `cbs_tables_search` |
| Rotterdamse raadsbesluiten | `ori_search(query="Rotterdam <topic>")` + **post-hoc filter op `records[].data.organization`** | **Geen native gemeente-filter** — `bestuurslaag="gemeente"` filtert op bestuursniveau, niet op stad |
| Ruimtelijke plannen op locatie | `ruimtelijke_plannen_search(gemeente="Rotterdam", status="vigerend", bbox=...)` | ✓ Werkt prima, geeft IMRO-id, viewer-URL, planType, status |
| Luchtkwaliteit-metingen | `luchtmeetnet_latest(component="NO2"\|"PM10"\|"PM2.5"\|"O3")` | ⚠️ Coords zijn `{lat:0, lon:0}` — alleen waarden bruikbaar, kaart-overlay niet mogelijk uit deze tool |
| Weer / aardbevingen | `knmi_*` (key vereist) | `KNMI_API_KEY` in env nodig |
| Waterstanden / scheepvaart | `rijkswaterstaat_waterdata_measurements(query=...)` | Query-syntax verlangt vaak station-naam (bv. "Hoek van Holland"), niet enkel stadsnaam |
| Bestemmingsplan-tekst / juridisch | DSO `dso_omgevingsdocumenten_search` (key vereist) | Discovery-only |
| Tweede Kamer / Officiële Bekendmakingen / Rechtspraak | `tweede_kamer_*` / `officiele_bekendmakingen_*` / `rechtspraak_search_ecli` | Nationale context bij ruimtelijke besluiten |
| BAG/Kadaster SPARQL | `bag_linked_data_select(sparql)` | Linked Data — power-user, voor specifieke joins |
| EU-data | `eurostat_*` / `data_europa_datasets_search` | Brede context |
| **Rotterdam-assets** (afval/bomen/lichtpunten/banken/containers/wegvakonderdelen) | `rotterdam.load_layer()` of `fetch_arcgis_layer(ARCGIS_LAYERS[...])` | **Niet in NL-GOV-MCP** — Obsurv = gemeente-eigen ArcGIS REST |
| **TIR-gebieden/buurten/subbuurten** | `rotterdam.load_layer("gebieden")` etc. | **Niet in NL-GOV-MCP** |
| **Kaart maken (PNG)** | `rotterdam.point_map` / `choropleth` + `finalize_map` + `save_map` | MCPs leveren data, geen kaarten |
| IMBOR-veldbetekenis / domeinwaarden | handmatig `.ttl` lezen | RDF/OWL, geen MCP |

Vuistregel: **NL-GOV-MCP voor nationale context (met directe tool, niet de router)**, **`rotterdam` package voor Rotterdam-specifieke assets + cartografie**.

## Bekende beperkingen NL-GOV-MCP

Geverifieerd via stdio integration-test 2026-05-26 (52 tools beschikbaar, alle connected):

1. **`nl_gov_ask` is geen smart router voor domain-intent**. "luchtkwaliteit Rotterdam vandaag" → routeert naar `data.overheid` catalog-search (0 resultaten) ipv `luchtmeetnet_latest`. Gebruik directe tools wanneer je de bron kent.

2. **`luchtmeetnet_latest` geeft `location: {latitude: 0, longitude: 0}`** in alle records. Endpoint levert wel `station_name` en `station_number` maar geen coords. Voor coords moet je apart de Luchtmeetnet stations-endpoint queryen (niet als MCP-tool beschikbaar). Pattern "luchtmeetstations op kaart" werkt dus niet end-to-end via deze MCP.

3. **`ori_search` heeft geen gemeente-filter**. `bestuurslaag="gemeente"` filtert op type bestuur, niet op stad. Resultaten over "Rotterdam afvalbeleid" bevatten bv. Stichtse Vecht-documenten. Post-hoc filteren op `records[].data.organization == "Gemeente Rotterdam"` is nodig.

4. **`data_overheid_datasets_search` dekt geen Rotterdam-eigen assets** (Obsurv). "rotterdam afvalbakken" → 0 datasets. Logisch — Rotterdam Obsurv is gemeente-API, niet in de nationale CKAN. Voor Rotterdam-data altijd `rotterdam.load_layer()` of `fetch_arcgis_layer()` gebruiken.

5. **`cbs_tables_search` keyword-relevance is fuzzy**. "wijken buurten 2024" geeft als top-hit een dataset over "wijken en buurten van Oss" (niet de nationale CBS Wijk- en Buurtkaart). Specificeer in query of gebruik `rotterdam.cbs_buurten_rotterdam(year=2024)` voor direct Rotterdam-geometry+inwoners.

6. **`bag_address_detail` retourneert soms `null`-velden** (oppervlakte_m2, bouwjaar) voor verblijfsobjecten waar Kadaster Individuele Bevragingen geen authoritative record heeft in lookup_only mode. Bv. Coolsingel 40 (stadhuis-omgeving) geeft `null`. Test altijd op `null` voordat je waarde gebruikt.

7. **`outputFormat` geadverteerd maar niet universeel**. Schema toont `outputFormat` op `nl_gov_ask`, `cbs_*`, `data_overheid_*`. **Niet** op `luchtmeetnet_latest`, `pdok_search`, `bag_*`, `ori_search`. Conversie naar geojson moet je dus zelf doen in Python (records → coord-extractie → GeoDataFrame).

8. **`rijkswaterstaat_waterdata_measurements`** verlangt vaak exacte station-naam in `query`. "waterstand Rotterdam" → 0 records. Werkt beter met "Hoek van Holland" of "Maeslantkering".

## Actief in deze omgeving

### `nl-gov-mcp` — 24 NL-overheidsbronnen, 52 tools

Repo: [WAINUTAI/NL-GOV-MCP](https://github.com/WAINUTAI/NL-GOV-MCP) (Apache 2.0, Node 22+).

Dekt: CBS, PDOK Locatieserver, PDOK BAG (+ Kadaster Individuele Bevragingen), Kadaster BAG SPARQL, data.overheid.nl (CKAN), NGR, Rechtspraak, Rijksoverheid, Rijksbegroting, DUO, KNMI, Luchtmeetnet, Rijkswaterstaat, NDW, ORI (Open Raadsinformatie), Ruimtelijke plannen (Wro/Bro), RDW, Tweede Kamer, Officiële Bekendmakingen, RCE Linked Data, Eurostat, data.europa.eu, DSO Omgevingsdocumenten, Overheid API register.

**Topvragen routeren via `nl_gov_ask`** — natural-date parsing (NL/EN, default tz `Europe/Amsterdam`), multi-source parallel, structured response (`summary`, `records[]`, `provenance`, `pagination`, optional `failures[]`).

Bekende individuele tools (uit README): `nl_gov_ask`, `cbs_tables_search`, `cbs_observations`, `data_overheid_datasets_search`, `duo_datasets_search`, `tweede_kamer_documents`, `tweede_kamer_search`, `officiele_bekendmakingen_search`, `rijksoverheid_search`, `rijksbegroting_search`, `overheid_api_register_search`. Andere connectors zijn aanwezig maar exacte tool-namen niet uit README — gebruik `nl_gov_ask` of MCP-tool-discovery.

**Output formats**: `json` (default), `csv`, `geojson`, `markdown_table`. Plus `dryRun` voor planning zonder uitvoer en `verbose` voor request-timings.

**API-keys nodig voor**: `KNMI_API_KEY`, `OVERHEID_API_KEY`, `DSO_API_KEY`. Rest werkt zonder keys.

#### Installatie (nog niet gedaan)

```bash
git clone https://github.com/WAINUTAI/NL-GOV-MCP.git ~/q-gis/nl-gov-mcp
cd ~/q-gis/nl-gov-mcp
npm ci && npm run build

# Registreer voor user-scope (stdio):
claude mcp add nl-gov --scope user -- node ~/q-gis/nl-gov-mcp/dist/src/index.js
# of met API-keys:
claude mcp add nl-gov --scope user --env KNMI_API_KEY=... -- node ~/q-gis/nl-gov-mcp/dist/src/index.js
```

Verificatie:
```bash
cd ~/q-gis/nl-gov-mcp && npm run test:questions   # offline fixtures
```

### `pdok` — Rotterdam-vriendelijke PDOK Locatieserver MCP

Lokaal gebouwd (`/Users/ds/q-gis/pdok-mcp/pdok_mcp.py`), geregistreerd onder user-scope. Geen API-key.

Tools (alle returneren RD én WGS84-coordinaten):

- `pdok__geocode(query, rows=5, type="any", binnen_gemeente=None)` — vrije-tekst adres / postcode / plaatsnaam zoeken. Filter `binnen_gemeente="Rotterdam"` om buiten-Rotterdam-hits te onderdrukken.
- `pdok__reverse_geocode(lat, lon, rows=1, type="adres")` — WGS84 → adres.
- `pdok__reverse_geocode_rd(x, y, rows=1)` — RD New → adres.
- `pdok__suggest(query, rows=10)` — autocomplete (lichter dan geocode, geen volledige record).
- `pdok__lookup(id)` — volledig record uit suggest-resultaten.

Voorbeeldoutput:
```json
{
  "id": "adr-...",
  "type": "adres",
  "label": "Coolsingel 40, 3011AD Rotterdam",
  "gemeente": "Rotterdam",
  "rd": {"x": 92539.4, "y": 437527.9},
  "wgs84": {"lat": 51.9227, "lon": 4.4792}
}
```

### Niet geo-gerelateerd, wel beschikbaar

Excalidraw, Mermaid, Gmail, Drive, Calendar.

## Geparkeerd

- **`gis-mcp`** (open-source, wraps shapely/geopandas/pyproj/rasterio/pysal). Geïnstalleerd in `/Users/ds/q-gis/gismcp werk/.venv/bin/gis-mcp` maar **niet** geregistreerd voor dit project. Gebruiker heeft besloten 'm niet te activeren — de `rotterdam` package dekt de cases lokaal.

- **`ogc-mcp-server`** ([hanzila1/ogc-mcp-server](https://github.com/hanzila1/ogc-mcp-server), GSoC 2026 / 52°North). Geëvalueerd 2026-05-26, **niet adopteren**.

  Concept: NL → OGC API bridge. Dekt OGC API Features / Processes / Records / EDR / Common. Dynamische tool-generatie: elk `/processes`-endpoint van de aangesloten OGC-server wordt automatisch een MCP-tool.

  Tools: `get_collections`, `get_features`, `get_collection_detail`, `discover_processes`, `execute_process`, `get_job_status`, `get_job_results`, `search_catalog`, `get_catalog_record`, `query_edr_position`, `query_edr_area`, `discover_ogc_server` + dynamisch gegenereerde process-tools.

  **Fit-analyse Rotterdam-bronnen** — dekt 1 van 6:

  | Bron | Protocol | Gedekt? |
  |---|---|---|
  | diensten.rotterdam.nl / Obsurv | ArcGIS REST FeatureServer | ❌ |
  | Rotterdam WFS-layers | WFS 2.0 | ❌ |
  | PDOK Locatieserver | eigen REST | ❌ (eigen `pdok` MCP doet dit) |
  | PDOK BAG/BGT | OGC API Features | ✅ |
  | CBS Buurten | WFS 2.0 | ❌ |
  | AHN3 | WCS | ❌ |

  **Blockers**:
  - 0 stars, solo dev, alpha-stage (GSoC-inzending).
  - Geen LICENSE-file in repo (README claimt Apache 2.0, GitHub API geeft `licenseInfo: null`).
  - `requirements.txt` is een pip-freeze dump: bevat `pywin32==311` zonder platform-marker → breekt install op macOS/Linux. Bevat ook `git-filter-repo` als runtime-dep.
  - Vendor-lock op Gemini (`google-genai`, `google-generativeai`) in een server die LLM-agnostisch zou moeten zijn.
  - Runtime-deps bevatten volledige `pygeoapi` + `Flask` + `rasterio` (bundled demo-backend, niet optioneel).

  **Verdict**: concept (NL → geospatiale-API bridge) is goed, deze implementatie te onvolwassen. Wachten op stabielere variant, of als nut blijft groeien zelf een dunne wrapper schrijven die ArcGIS REST + WFS 2.0 dekt — dáár zit de echte gap voor Rotterdam-data.

## Wanneer MCP, wanneer Python

**Gebruik MCP** als:
- De gebruiker tijdens een gesprek iets opzoekt ("waar ligt X?", "wat is het adres bij coord Y?")
- Een eenmalige operatie geen script-runtime rechtvaardigt
- Het resultaat in de conversatie moet zichtbaar zijn

**Gebruik de `rotterdam` package** als:
- Het onderdeel is van een batch / reproduceerbaar script
- Je meerdere lookups combineert met andere geopandas-bewerkingen
- Snelheid / caching belangrijk is (MCP overhead per call ~50-200ms)

Beide hitten dezelfde Locatieserver-endpoint — semantiek is identiek.

## Mogelijke toekomstige MCPs

Niet bouwen tenzij concreet nodig:

| Idee | Wanneer overwegen |
|------|-------------------|
| `cbs-statline` MCP | Als je vaak socio-economische indicatoren per buurt opvraagt zonder Python |
| `rotterdam-assets` MCP (Obsurv-wrapper) | Als de skill ook buiten dit project gebruikt wordt |
| 3D BAG / AHN raster-MCP | Specifiek werk met gebouwhoogtes |

## Server bijwerken

```bash
# Code bewerken:
$EDITOR /Users/ds/q-gis/pdok-mcp/pdok_mcp.py

# Dependencies:
cd /Users/ds/q-gis/pdok-mcp && source .venv/bin/activate && uv pip install ...

# Claude Code herstart oppikt nieuwe code automatisch (stdio).
```

Deregistreren: `claude mcp remove pdok --scope user`.
