# Databronnen

## Overzicht

Dit document zet de beschikbare GIS-databronnen uit het aangeleverde bronbestand om naar Markdown.

Er zijn twee hoofdgroepen:

- **TIR**: territoriale referentielagen van Rotterdam
- **Assets**: beheerlagen van objecten in de openbare ruimte

## Formaten en gebruik

Per bron zijn er meestal meerdere toegangsvormen:

- **ArcGIS REST MapServer**: handig voor verkenning en gebruik in ArcGIS-software
- **WFS (OGC)**: het meest geschikt voor QGIS en andere GIS-software die open standaarden gebruikt
- **JSON / pjson**: nuttig voor inspectie, scripting en API-gebruik

## TIR

### ArcGIS REST

- TIR totaal: https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer
- Gemeente: https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/0
- Gebieden: https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/1
- Buurten: https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/2
- Subbuurten: https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/3
- Subbuurtdelen: https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/4

### WFS

- TIR WFS GetCapabilities: https://diensten.rotterdam.nl/arcgis/services/SB_BI/TIR/MapServer/WFSServer?request=GetCapabilities&service=WFS

## Assets

### Algemene mapverwijzing

- Folder: `SB_Infra`

### ArcGIS REST MapServer

- Wegvakonderdelen: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Wegvakonderdelen/MapServer
- Lichtmasten: niet ingevuld in bronbestand
- Lichtpunten: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/LICHTPUNTEN/MapServer
- Bomen: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Bomen/MapServer
- Banken: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Banken/MapServer
- Afvalbakken: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Afvalbak/MapServer
- Containers: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Container/MapServer

### WFS en JSON varianten

#### Bomen

- WFS: https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Bomen/MapServer/WFSServer?request=GetCapabilities&service=WFS
- JSON: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Bomen/FeatureServer?f=pjson

#### Afvalbakken

- WFS: https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Afvalbak/MapServer/WFSServer?request=GetCapabilities&service=WFS
- JSON: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Afvalbak/MapServer?f=pjson

#### Banken

- WFS: https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Banken/MapServer/WFSServer?request=GetCapabilities&service=WFS
- JSON: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Banken/MapServer?f=pjson

#### Lichtpunten

Opmerking uit het bronbestand: hierin zitten lantarenpalen, maar ook grondspots.

- WFS: https://diensten.rotterdam.nl/arcgis/services/SB_Infra/LICHTPUNTEN/MapServer/WFSServer?request=GetCapabilities&service=WFS
- JSON: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/LICHTPUNTEN/MapServer?f=pjson

#### Wegvakonderdelen

- WFS: https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Wegvakonderdelen/MapServer/WFSServer?request=GetCapabilities&service=WFS
- JSON: https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Wegvakonderdelen/MapServer?f=pjson

## Laden in GIS-software

## QGIS

### WFS-bronnen

1. Ga naar `Layer` -> `Add Layer` -> `Add WFS / OGC API - Features Layer`.
2. Maak een nieuwe verbinding.
3. Plak de gewenste `WFSServer?...GetCapabilities...` URL.
4. Klik op `Connect`.
5. Selecteer de laag en voeg die toe.

### ArcGIS REST-bronnen

QGIS kan sommige ArcGIS REST services lezen via extra providers of plugins, maar WFS is meestal de meest robuuste route.

## ArcGIS Pro

1. Voeg een ArcGIS Server connection toe of gebruik de REST MapServer URL.
2. Voor open standaarden kun je ook de WFS-endpoints toevoegen.
3. Kies per laag of je vooral wilt visualiseren, bevragen of exporteren.

## Praktisch advies

- Gebruik **WFS** als je maximale interoperabiliteit wilt.
- Gebruik **ArcGIS REST** als je in de ESRI-stack werkt.
- Gebruik **pjson** alleen voor inspectie, documentatie of scripting.

## Relatie met IMBOR

Deze databronnen zijn de feitelijke geoservices. De IMBOR-bestanden in deze workspace vormen vooral het **semantische model** achter objecttypen, eigenschappen en domeinwaarden.

In de praktijk betekent dit:

- laad de TIR- en assetlagen in GIS
- gebruik IMBOR om velden en objecten te interpreteren
- maak indien nodig een mapping van servicevelden naar IMBOR-concepten