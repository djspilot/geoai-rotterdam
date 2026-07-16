# Cartografische Richtlijnen & Meetniveaus

Required reading whenever you make a map. The Rotterdam standard follows the *Geo-visualisatie* Wikibooks Deel B (visualisatie) en Deel C (kaartopmaak).

## Meetniveaus (Measurement Levels)

| Niveau | Type | Beschrijving | Voorbeelden |
|--------|------|-------------|-------------|
| **Nominaal** | Categorisch | Categorieën zonder volgorde | TYPE asset, BUURTNAAM |
| **Ordinaal** | Categorisch | Categorieën mét rangorde | Conditieklasse, tevredenheid |
| **Interval** | Numeriek | Gelijke afstanden, geen nul | Temperatuur, jaartal |
| **Ratio** | Numeriek | Gelijke afstanden + absoluut nul | Aantal, lengte, oppervlakte |

Rules:
- Nominaal / Ordinaal → categorische kleuren, géén choropleet op ruwe counts.
- Interval / Ratio → sequentieel of divergerend palet, rekenen mag.
- Choropleet → **altijd normaliseren** (per km² of per 1000 inwoners). Nooit ruwe totalen per gebied.

## Verplichte kaartelementen

1. **Titel** bovenaan met onderwerp + locatie + (indien bekend) periode.
2. **Legenda** met alle afgebeelde objecten. Ontbrekende waarden labelen als `"Waarde onbekend"`.
<!-- 3. **Schaalstok** in metrische eenheden, afgerond. -->
4. **Projectie**: kaarten over NL altijd in **EPSG:28992**. Geen Mercator.
5. **Laagvolgorde**: punten > lijnen > vlakken (punten bovenaan).
6. **Labels**: dunne witte halo wanneer ondergrond bont is.
7. **Contrast**: aparte kleuren per objecttype.
8. **Classificatie**: max 5 klassen (absoluut max 9), grenzen op ronde getallen.
9. **Normalisatie**: voor choropleet altijd / inwoners of oppervlak.
10. **Palet**: sequentieel voor oplopend, divergerend voor afwijkingen. Gebruik ColorBrewer.

`rotterdam.style_map(ax, title)` zet de titel (+ subtitel via `subtitle=`). Noordpijl en schaalstok staan **standaard uit** — alleen aanzetten wanneer nodig (invarianten 13/14).

## Map type beslisboom

| Data situatie | Beste kaarttype | rotterdam functie |
|---------------|-----------------|-----------------|
| < 5000 punten, exact locaties | Point map | `point_map()` |
| > 5000 punten, citywide | Hexbin of kleine scatter met alpha | matplotlib hexbin |
| Waarde per gebied (genormaliseerd) | Choropleth, sequentieel | `choropleth()` |
| Afwijking van centraal punt | Choropleth, divergerend | `choropleth(cmap="RdBu")` |
| Proportionele grootte per locatie | Scaled symbol (cirkel-oppervlak ∝ waarde) | matplotlib scatter `s=` |
| Twee variabelen per gebied | Bivariate choropleth of zij-aan-zij | twee `choropleth()` calls |
| Categorische verdeling | Dot map met kleur per categorie | `point_map()` per categorie |

## Standaard styling

Alle defaults zitten in `rotterdam.STYLE`. Aanpassen op één plek = elke kaart verandert. Defaults:

- **Font**: Helvetica Neue / Helvetica / Arial / DejaVu Sans (eerst beschikbare).
- **Titel**: 16pt bold, donkergrijs `#1a1a1a`, links uitgelijnd, pad 14.
- **Subtitel**: 10.5pt normaal (nooit vet), grijs `#555`, boven de kaart onder de titel.
- **Footer**: 7.5pt, lichtgrijs `#888`, met dunne separator daarboven.
- **Figure size**: stad `(12, 10)` of `(14, 12)`; gebied/buurt `(10, 10)` of `(12, 12)`.
- **Markersize**: stadbreed dens `0.3–1`; gebied/buurt `2–6`.
- **Boundary**: `#666666`, linewidth `0.5`.
- **Polygon fill**: `#f6f3ee` (licht neutraal).
- **Background**: figure wit `#fff`, axes `#fafafa`.
- **Asset accenten**: zie `rotterdam.ASSET_COLORS`.
- **Output**: PNG @ 150 dpi naar `output/`; SVG alleen bij expliciete vraag.

## Pipeline voor nette kaarten

Vier verplichte stappen, in deze volgorde:

```python
fig, ax = point_map(data, boundary=..., title="…", subtitle="…")   # of choropleth(...)
finalize_map(fig, source="Obsurv via diensten.rotterdam.nl",
             date="2026-05-12",                # auto bij None
             suptitle=None,                    # optionele pagina-titel
             author="DS")                      # optioneel
warns = validate_map(fig, ax, data=data, normalized=True)
save_map(fig, "naam")
```

`finalize_map` regelt: footer met bron + datum, dunne separator, marges, optionele suptitle/subtitle.
`validate_map` checkt titel, legenda, CRS, normalisatie/klassen, **bronvermelding**, **titelhiërarchie** (hoofdtitel vet, subtitel niet vet) en **NL-getalnotatie** — fix de warnings vóór `save_map`.

## Default kaartoutput

- Statische kaarten (`matplotlib + geopandas`) → PNG/SVG via `save_map()`.
- Interactief alleen wanneer de gebruiker er expliciet om vraagt (Folium).
