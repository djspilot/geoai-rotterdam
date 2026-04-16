# General Data Flowchart

Dit diagram beschrijft wat er in `General data` staat en hoe de bestanden inhoudelijk met elkaar samenhangen.

```mermaid
flowchart TD
    A[General data] --> B[Data]
    A --> C[context]
    A --> D[Teams]
    A --> E[overig]
    A --> F[download_rotterdam_data.py]

    B --> B1[tir_gemeente.geojson]
    B --> B2[tir_gebieden.geojson]
    B --> B3[tir_buurten.geojson]
    B --> B4[tir_subbuurten.geojson]
    B --> B5[tir_subbuurtdelen.geojson]
    B --> B6[afvalbak.geojson]
    B --> B7[bomen_chunks]
    B --> B8[bomen_chunks.log]

    B1 --> G[TIR territoriale referentie]
    B2 --> G
    B3 --> G
    B4 --> G
    B5 --> G

    B6 --> H[Rotterdam assetdata]
    B7 --> H

    C --> C1[Context.md]
    C --> C2[Databronnen-WFS.md]
    C --> C3[QGIS-Guide.md]

    C1 --> I[Uitleg over IMBOR, TIR en GIS-context]
    C2 --> J[Overzicht van REST, WFS en JSON databronnen]
    C3 --> K[QGIS-workflow voor laden en analyseren]

    D --> D1[IMBOR-2025]
    D1 --> D2[IMBOR2025.accdb]
    D1 --> D3[LinkedData TTL files]
    D1 --> D4[Zip-archieven]

    D2 --> L[Tabulair model in Access-formaat]
    D3 --> M[Semantisch model: vocabulaire, kern, domeinwaarden, geometrie]
    D4 --> N[Distributiebestanden]

    E --> E1[Context.docx]
    E --> E2[Databronnen WFS.docx]
    E --> E3[IMBOR-2025.zip]
    E --> E4[load_rotterdam_wfs_qgis.py]

    E1 --> O[Bronbestand voor contextsamenvatting]
    E2 --> P[Bronbestand voor databronnenlijst]
    E3 --> Q[Origineel archief]
    E4 --> R[PyQGIS script om WFS-lagen te laden]

    F --> S[Python downloader via ArcGIS REST query]
    S --> B

    G --> T[Gebruik in GIS: gebieden, buurten, aggregatie, joins]
    H --> U[Gebruik in GIS: objectlocaties en tellingen]
    I --> V[Interpretatie van de mapinhoud]
    J --> V
    K --> V
    L --> W[Gebruik als lookup of export naar CSV]
    M --> X[Gebruik als semantische referentie, niet als kaartlaag]

    T --> Y[QGIS analyse en kaarten]
    U --> Y
    W --> Y
    X --> Y
    V --> Y
```

## Leeshulp

- `Data` bevat de **lokale GIS-bestanden** die direct bruikbaar zijn in QGIS of Python.
- `context` bevat de **uitlegdocumenten** die beschrijven wat de data is en hoe je die gebruikt.
- `Teams/IMBOR-2025` bevat het **IMBOR-model** als Access-database en Linked Data.
- `overig` bevat de **ruwe bronbestanden** en een PyQGIS-script.
- `download_rotterdam_data.py` is de schakel tussen de online Rotterdam-services en de lokale bestanden in `Data`.

## Kernboodschap

De map combineert vier soorten informatie:

1. **Lokale GIS-data** voor directe analyse
2. **Contextdocumentatie** voor begrip en workflow
3. **IMBOR referentiemodel** voor semantiek en domeinwaarden
4. **Scripts** om data in te laden of te downloaden

Samen vormen die een workflow van brondata en modelinformatie naar QGIS-analyse en kaartproductie.