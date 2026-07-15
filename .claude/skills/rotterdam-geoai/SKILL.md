---
name: rotterdam-geoai
description: Use when working with Rotterdam municipality GIS data, IMBOR 2025 asset management model, TIR territorial boundaries, Dutch public space (beheer openbare ruimte) datasets, or when asked to create maps/visualizations of Rotterdam assets. Triggers on Rotterdam geodata, WFS services, ArcGIS REST endpoints, IMBOR vocabulary, TIR gebieden/buurten, QGIS workflows, or questions like "toon op kaart", "maak een kaart", "where are the trees", "hoeveel per wijk".
---

# Rotterdam GeoAI

End-to-end skill voor het beantwoorden van GIS-vragen over Rotterdam: data ophalen, opschonen, koppelen aan TIR / CBS, en publiceren als kaart volgens de Rotterdamse kartografische richtlijnen.

## Quickstart

De canonieke library woont in het project zelf, niet in de skill:

```
C:\Users\134020\Downloads\geoai-rotterdam-main\General data\rotterdam\
```

```python
import sys
sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")
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
4. **Kaart heeft altijd** titel, legenda, projectie. Schaalstok is optioneel (`style_map(..., scalebar=True)`). `style_map(ax, title)` regelt dit.
5. **Default output**: statische PNG via `save_map()`. Folium pas op expliciet verzoek.
6. **Rotterdam Zuid/Noord**: gebruik `ROTTERDAM_ZUID_GEBIEDEN` / `ROTTERDAM_NOORD_GEBIEDEN`. Vermeld de definitie in caption of script-output.
7. **Data niet gevonden?** Kun je de gevraagde data niet vinden in de skill (`LOCAL_FILES`, `ARCGIS_LAYERS`, de ArcGIS-server van Rotterdam, of de gedocumenteerde nationale bronnen in `national_sources.md`/`mcp_notes.md`), ga dan **niet** zomaar zelf het internet op. **Vraag eerst de gebruiker** of hij (a) open-dataportalen op het internet wil laten doorzoeken, of (b) wil stoppen. Pas na akkoord voor (a) verder zoeken.
8. **Legenda nooit over de data.** De legenda mag nooit datapunten/symbolen op de kaart overlappen (en ook niet de noordpijl of schaalstok — de kaartelementen). Gebruik `place_legend(ax, ..., corner="auto")`: die **ontwijkt automatisch álle geplotte lagen** op de assen (scatter-punten, lijnen, gevulde vlakken) — nooit de basemap of de kaartelementen. Je hoeft geen `data=` mee te geven; wil je iets extra's ontwijken, geef dan `data=<GeoDataFrame/punten of een lijst van lagen>`. **Plaatsing volgt een vaste prioriteit:**
   - **hoek-methode**: eerste vrije hoek in de volgorde **linksonder → linksboven → rechtsonder → rechtsboven** (een hoek waar alleen een kaartelement zit, wordt er net boven/onder gebruikt);
   - **kant-methode**: lukt geen hoek, dan schuift de legenda langs een rand naar de eerste vrije plek, randen in de volgorde **links → rechts → onder → boven**;
   - **zijpaneel-methode**: lukt ook dat niet, dan waarschuwt de routine → zet de legenda in een **zijpaneel**. Voor een kleurstaal-legenda gebruik je hiervoor **`add_swatch_legend_sidepanel(fig, ax, colors, labels, ...)`**: die maakt het paneel **precies zo breed als de legenda + marge** (totale figuurbreedte = kaart + gap + legenda + marge, dus geen overbodige witruimte naast de legenda). Voor een vrije/andere paneelinhoud (bv. een genummerde naamlijst): teken in een `add_side_panel()` en roep dáárna **`fit_side_panel(fig, ax, panel)`** aan — die krimpt het paneel tot de werkelijk getekende inhoud + marge. NB: witruimte naast een zijpaneel gaat **niet** weg met `bbox_inches="tight"` van `save_map` (die rekent de volle paneel-as mee, ook met een onzichtbaar achtergrondvlak) en ook niet doordat de footer tot ~0.95 van de figuurbreedte loopt — alleen een smaller paneel (via bovenstaande helpers) haalt de witruimte echt weg.
   
   **Volgorde is cruciaal:** roep `place_legend`/`add_*_legend` aan **ná** `add_scalebar`/noordpijl **én ná** `finalize_map` + `fit_figure_to_data`. Anders meet de routine de legenda op de nog-niet-definitieve figuurhoogte en klopt de plaatsing niet met de uiteindelijke kaart.
9. **Proportionele-symbool legenda's**: gebruik `add_proportional_legend(ax, values, sizes=<zelfde s als ax.scatter>, corner="auto", data=...)`. Die tekent de cirkels op ware kaartgrootte met **gelijke witruimte tussen de cirkelranden** (constante tussenafstand; matplotlib's eigen legenda kan alleen de middelpunten gelijk spatiëren, wat ongelijke gaten geeft) op een passend kader, met dezelfde auto-plaatsing als invariant 8.
10. **Basemap standaard in kleur.** Begin standaard met de gekleurde Rotterdamse basemap: `add_rotterdam_basemap(ax, layer="kleur")` (met PDOK-fallback `add_pdok_basemap(ax, layer="standaard")`). Kies alleen een andere laag (`grijs`, `luchtfoto`) als de gebruiker daarom vraagt of als kleur de data onleesbaar maakt — meld dat dan kort.
11. **AI-disclaimer in de footer.** Elke kaart toont in de footer altijd "Disclaimer: deze kaart is gemaakt met AI." `finalize_map()` voegt dit automatisch toe — niet handmatig weghalen. `finalize_map()` zet daarnaast rechts-uitgelijnd "Gemeente Rotterdam" (uitgever) aan de rechterrand van de footer. Past de bron/datum/disclaimer + uitgever niet op één regel (bv. lange bron of smalle kaart), dan breekt de footer automatisch over meerdere regels af; scheidingslijn en ondermarge schuiven mee.
12. **Basemap-bronvermelding alleen voor derden.** De eigen Rotterdamse basemaps (`add_rotterdam_basemap`) hoeven **niet** in de bronregel (`finalize_map(source=...)`) — ze zijn onze eigen huisstijl. Achtergronden van andere partijen (PDOK BRT via `add_pdok_basemap`, luchtfoto's van derden, OSM-tegels, enz.) **wel** vermelden. Bouw `source` dus zo op dat de Rotterdam-basemap niets toevoegt en alleen een fallback/derde-partij-basemap een "Basiskaart: …"-deel krijgt.
13. **Noordpijl alleen wanneer nodig.** Een noordpijl is **alleen noodzakelijk** als het noorden **niet recht naar boven wijst** (bv. een gedraaide kaart) of als de kaart voor **navigatie** is gemaakt. Een gewone noord-boven kaart — de standaard, want alles in EPSG:28992 is noord-boven — krijgt **géén** noordpijl. `style_map` tekent daarom **standaard geen** noordpijl (`north=False`). Is een pijl wél nodig, dan zet je `style_map(ax, title, north=True)` (of `north="upper right"`) en staat hij aan de **bovenzijde**: bij voorkeur **linksboven**, en **rechtsboven** als de linkerbovenhoek bezet is (bv. door de legenda of belangrijke data). Los kan ook met `add_north_arrow(ax, corner=...)`. Nooit onderaan of in het midden. **Twee varianten** (zelfde vorm/plaatsing): **Noordpijl A** (`variant="A"`, default) is tweekleurig (linkerhelft zwart, rechterhelft wit); **Noordpijl B** (`variant="B"`) is **volledig zwart**. Kies via `add_north_arrow(ax, variant="B")` of `style_map(ax, title, north=True, north_variant="B")`.
14. **Schaalstok alleen wanneer nodig.** Een schaalstok is **alleen nodig** als de kaart voor **navigatie** is of als **afstand relevant** is voor de interpretatie (bv. dichtstbijzijnde-voorziening / serviceradius, buffer- of afstandsanalyse). Bij thematische of overzichtskaarten waar het om waarden of indeling gaat (choropleet, puntenoverzicht, grenzen) laat je de schaalstok **weg**. `style_map` tekent daarom **standaard geen** schaalstok (`scalebar=False`). Is een schaalstok wél nodig, dan staat hij aan de **onderzijde**: bij voorkeur in de **linkeronderhoek** (`add_scalebar(ax, inside=True)`), anders rechtsonder (`add_scalebar(ax, inside=True, location="lower right")`); nooit bovenaan of in het midden. **Standaard geen kader** (`box=False`) — de balk staat direct op de basemap, labels met een witte halo; alleen met `box=True` komt er een wit kader omheen. **Twee varianten** (zelfde lengte/labels/plaatsing): **A** (`variant="A"`, default) is een **geblokte balk**; **B** (`variant="B"`) is **één enkele lijn met verticale streepjes** bij elke segmentgrens. Kies via `add_scalebar(ax, variant="B")` of `style_map(ax, title, scalebar=True, scalebar_variant="B")`.
15. **Vaste marge tussen kaartelementen.** Tussen kaartelementen (titel, legenda, noordpijl, schaalstok, zijpaneel) zit altijd een **horizontale én verticale afstandsmarge**, en die is **gelijk aan de marge tot de kaartrand** (horizontaal `LEGEND_MARGIN[0]`, verticaal `MARGIN_IN`). Ze mogen elkaar dus niet alleen niet overlappen maar ook niet raken. De legenda-plaatsing (invariant 8) blaast daarvoor de gereserveerde zones van noordpijl/schaalstok met die marge op. Controleer bij een handmatige lay-out altijd of elk kaartelement dezelfde marge tot zijn buren én tot de rand houdt.
16. **Getalnotatie volgens de regionale (NL) instellingen.** Gebruik in alle labels/legenda's/teksten de Nederlandse getalnotatie: **duizendtalscheiding met punt** en **decimaal met komma** (bv. `20.028`, `1.957`, `1,5 km`, `6.024 inw./km²`). Nooit de Engelse notatie (`20,028` / `1.5`). Formatteer met de gedeelde helper **`nl_getal(v, decimalen=0)`** uit `rotterdam` (`from rotterdam import nl_getal`) i.p.v. rauwe `str(getal)` of ad-hoc `f"{v:,}"`. `add_proportional_legend`/`add_swatch_legend` gebruiken deze notatie al standaard.
17. **Titelhiërarchie.** Vaste rangorde in de teksten boven de kaart:
    1. De **hoofdtitel** is **altijd vetgedrukt**.
    2. De hoofdtitel heeft een **groter lettertype dan de subtitel**.
    3. De **subtitel is dus nooit vetgedrukt** (en grijzer/kleiner).
    4. Bij een kaart met meerdere **deelkaarten** (panelen) heeft de overkoepelende hoofdtitel een **groter lettertype dan de titel van elke deelkaart**; de deelkaart-titels zijn visueel ondergeschikt aan de hoofdtitel.

    `style_map`/`finalize_map` regelen dit via `STYLE`: `suptitle_size` (19, vet) voor de overkoepelende hoofdtitel bij meerdere deelkaarten > `title_size` (16, vet) voor de (deelkaart)titel / de hoofdtitel van een enkele kaart > `subtitle_size` (10,5, **normaal**). Overschrijf deze maten niet zó dat de rangorde omdraait. NB "hoofdtitel" = wat matplotlib *suptitle* noemt.
18. **Titel en subtitel boven de kaart.** De (hoofd)titel en de subtitel **overlappen nooit met de kaart** — ze staan er **samen bóven** (titel boven, subtitel er direct onder, allebei boven de kaartrand). `style_map` regelt dit: de subtitel wordt met `va="bottom"` net boven de kaartrand gezet en de titel-`pad` overspant de subtitel. Zet een subtitel dus niet zelf met `va="top"` op `y=1.0` (dan hangt hij ín de kaart); geef hem mee via `style_map(ax, titel, subtitle=…)` of plaats hem op dezelfde manier boven de as. Geldt ook voor de hoofdtitel + subregel op figuurniveau (`finalize_map(suptitle=…, suptitle_subtitle=…)`), die al boven de panelen staan.

## Beslisboom: van vraag naar kaart

1. **Wat is gevraagd?** locaties tonen / vergelijken / verdeling / dichtheid / relatie tot ander attribuut.
2. **Welke data?** Eerst `LOCAL_FILES` (snel). Anders `fetch_arcgis_layer(ARCGIS_LAYERS[...])`. Voor inwoneraantallen → `cbs_buurten_rotterdam()`. Voor adressen → `pdok_geocode_rd()`. **Niet gevonden in de skill/Rotterdam-server/nationale bronnen? → invariant 7: vraag de gebruiker (internet doorzoeken of stoppen), ga niet ongevraagd zelf zoeken.**
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
geoai-rotterdam-main\.claude\skills\rotterdam-geoai\
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
geoai-rotterdam-main\General data\rotterdam\
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

**`rotterdam.cartography`** — `point_map`, `choropleth` → `(fig, ax)`. Pipeline: `point_map`/`choropleth` → `finalize_map(fig, source=..., date=...)` → `validate_map(fig, ax, data=...)` → `save_map(fig, "naam")` (default → `output/maps/naam.png`). Building blocks: `style_map`, `add_scalebar(ax, inside=True)` (schaalstok in de kaart) of `add_scale_ratio(ax, loc=...)` (schaalgetal '1:x' i.p.v. balk; ná de definitieve lay-out aanroepen), `add_north_arrow` (driehoek, linksboven op `LEGEND_MARGIN`), `add_rotterdam_basemap(ax, layer="grijs"|"kleur"|"luchtfoto")` (Rotterdamse huisstijl-basemap / luchtfoto), `add_pdok_basemap(ax, layer=...)` (landelijke PDOK BRT via nlmaps), `setup_headless_matplotlib`. Tegen witruimte: `finalize_map(..., tight_bottom=True)` (kleinere ondermarge; alleen met een `inside`-schaalstok) + `fit_figure_to_data(fig, ax)` (figuurhoogte op de gebiedsvorm; ná `finalize_map`, vóór het meten van een legenda/lijst-kader). Legenda vs. data-overlap: `place_legend(ax, handles=..., corner="auto", data=...)` (kiest de leegste hoek), of — als de legenda in geen hoek/rand past — een **zijpaneel** náást de kaart (kaart blijft ongewijzigd), ná `finalize_map`/`fit_figure_to_data`. Voor een kleurstaal-legenda: `add_swatch_legend_sidepanel(fig, ax, colors, labels, title=..., legendakop=..., fontsize=...)` — meet de legenda en maakt het paneel exact zo breed (kaart + gap + legenda + marge, geen witruimte ernaast). Voor vrije paneelinhoud: teken in `add_side_panel(fig, ax, width_in=...)` en roep daarna `fit_side_panel(fig, ax, panel)` aan — die krimpt het paneel tot de getekende inhoud + marge (nodig omdat `save_map`'s tight-bijsnijding de volle paneel-as meerekent).

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
