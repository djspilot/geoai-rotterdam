# Veelgemaakte fouten

## CRS

- **GeoJSON met EPSG:4326-metadata maar RD-coordinaten**: classieke Rotterdam-bug. Gebruik `load_rotterdam()` / `load_layer()`, nooit een blinde `to_crs()`.
- **`set_crs(epsg=28992)` op laag die al CRS heeft** → `ValueError`. De loader checkt dit; gebruik hem.
- **EPSG:28992 in Folium**: web maps verwachten WGS84. Reproject naar `WGS84` voor Folium.

## Veldnamen in asset-lagen

- `WIJK` is de **TIR-buurt**, `BUURT` is de **TIR-subbuurt**. Filteren op `WIJK='Stadsdriehoek'` selecteert de hele TIR-buurt. Filteren op `BUURT` selecteert een subbuurt-onderverdeling.

## Gebiedsafbakening

- "Rotterdam Zuid" filteren op `WOONPLAATS IN ('Charlois','Feijenoord','IJsselmonde')` mist **Hoogvliet, Pernis, Rozenburg, Waalhaven-Eemhaven, Vondelingenplaat**. Gebruik `ROTTERDAM_ZUID_GEBIEDEN`.
- Voer ook een spatial join uit ter verificatie — `WOONPLAATS` kan vervuild zijn.

## Geometrie-edge-cases

- TIR-lagen bevatten soms features met `geometry IS NULL` of `is_empty`. Gebruik `safe_centroids()`.
- Spatial joins op verkeerde CRS geven stilzwijgend lege resultaten — beide GeoDataFrames in EPSG:28992 voor accurate Dutch metric distance.

## Choropleth-fouten

- **Ruwe counts per buurt** → misleidend (Schiekade groter dan Oude Westen ≠ meer assets). Altijd `/inwoners` of `/oppervlak`. `count_per_polygon(..., normalize_by="aantal_inwoners")`.
- **Te veel klassen** (> 9). 5 is de standaard.
- **Mercator-projectie** voor NL-kaart in matplotlib. Gebruik EPSG:28992.

## ArcGIS download

- **`outSR` vergeten** → defaultwaarde van service, kan EPSG:4326 zijn. Geef altijd `outSR=28992`.
- **Geen paginatie** op grote lagen (bomen 200k features) → server kapt af op 1000–2000. Gebruik `fetch_arcgis_layer()`.
- **SSL-fouten** op `diensten.rotterdam.nl`. Helpers schakelt verificatie standaard uit.

## Matplotlib

- `plt.cm.get_cmap("YlOrRd", n)` is **deprecated** sinds matplotlib 3.7. Gebruik `plt.colormaps.get_cmap("YlOrRd").resampled(n)`.
- Vergeet niet `setup_headless_matplotlib()` te callen bij script-mode.

## Folium

- 100k+ punten individueel plotten = browser crash. Gebruik `MarkerCluster` of `HeatMap` of switch naar statisch.

## IMBOR

- `.ttl` is **geen GIS-laag**. Niet proberen te openen in QGIS als vectorlaag. Het is een RDF-schema voor veldbetekenis en domeinwaarden.

## CBS

- `aantal_inwoners == -99999999` betekent "geheimgehouden" (kleine aantallen). `cbs_buurten_rotterdam()` filtert deze al.
- CBS `buurtcode` ≠ TIR `BUURT`. Joinen op geometrie, niet op code.
