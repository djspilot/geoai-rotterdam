# Context

## What this information is

This workspace combines two different kinds of information:

1. **IMBOR 2025 model files**
   - `IMBOR2025.accdb` is a Microsoft Access database containing the IMBOR 2025 model.
   - The `.ttl` files are **Linked Data / RDF / OWL** distributions of IMBOR 2025.
   - These files describe the **information model, vocabulary, classes, properties, domain values, and addenda** for public-space asset management.
   - They are **not a ready-to-use GIS feature dataset** with map layers by themselves.

2. **Rotterdam GIS context and source services**
   - The context document describes how Gemeente Rotterdam uses:
     - **IMBOR** as the semantic standard for beheer openbare ruimte.
     - **TIR** (Territoriale Indeling Rotterdam) as the territorial reference dataset.
     - Asset data published through ArcGIS services, including WFS and JSON endpoints.

## IMBOR in plain language

**IMBOR** stands for **Informatiemodel Beheer Openbare Ruimte**. It is a Dutch standard developed by CROW for recording and exchanging information about objects in public space in a consistent way.

Examples of covered domains include:

- roads
- greenery
- lighting
- waste containers
- trees
- sewer and utility-related objects

The Linked Data package shows that IMBOR 2025 is published as a set of ontologies and vocabularies, including:

- **Vocabulaire**: terms and labels
- **Kern**: core classes and properties
- **Domeinwaarden**: code lists / controlled values
- **Aanvullend metamodel**: additional IMBOR-specific metadata concepts
- **Addendum geometrie**: geometry-related shapes and constraints
- **Addendum materie**: material-related concepts
- **Addendum OAGBD**: lifecycle-phase typing
- **Addendum referentiemodellen**: links to external reference models
- **MIM**: MIM mappings / equivalents

## TIR in plain language

**TIR** stands for **Territoriale Indeling Rotterdam**. It is the municipal territorial reference structure of Rotterdam.

It contains administrative boundaries and codes for levels such as:

- gemeente
- gebied
- buurt
- subbuurt
- subbuurtdeel

The context notes that Rotterdam uses TIR as a reference dataset for presenting socio-economic statistics and asset-management information.

## What the files in this workspace mean

### Linked Data files

The `.ttl` files are Turtle serializations of RDF data. They can be loaded into:

- a triple store such as GraphDB, Fuseki, Stardog, or Blazegraph
- semantic tools that support RDF/OWL and SPARQL
- GIS software only after conversion or through a semantic workflow

These files are mainly useful for:

- understanding the IMBOR schema
- mapping local datasets to IMBOR concepts
- querying the model through SPARQL
- validating or documenting data structures

### Access database

`IMBOR2025.accdb` is a Microsoft Access file. It is useful as a tabular model distribution, but on macOS it is not directly as convenient as on Windows.

It can be used to:

- inspect tables in Microsoft Access on Windows
- read tables through ODBC-compatible tools if drivers are available
- export tables to CSV for further use in GIS or data engineering workflows

## How to load this in GIS software

## 1. TIR and asset services

These are the easiest parts to load in GIS software because they are web map / feature services.

### In QGIS

- For **WFS** sources: use `Layer` -> `Add Layer` -> `Add WFS / OGC API - Features Layer`.
- Create a new connection and paste the **WFSServer GetCapabilities URL**.
- Connect, choose the layer, and add it.

### In ArcGIS Pro

- Add the ArcGIS REST service URL directly as a server connection or use the WFS endpoint.
- For MapServer URLs, ArcGIS usually handles them directly.

## 2. IMBOR Linked Data (`.ttl`)

These Turtle files are **not standard GIS vector layers** like GeoPackage, Shapefile, GeoJSON, or WFS layers.

To use them in GIS, one of these approaches is typical:

- Load them into a triple store and query with SPARQL.
- Convert RDF resources with geometry into GeoJSON or CSV first.
- Use them as a **reference model** while loading actual spatial datasets from WFS/FeatureServer.

Important note:

- Although `imbor2025-addendum-geometrie.ttl` references geometry-related concepts, the package here appears to be primarily a **schema/model publication**, not a spatial dataset of Rotterdam assets.

## 3. IMBOR Access database (`.accdb`)

Possible workflow:

- Open on Windows with Microsoft Access.
- Export relevant tables to CSV.
- In QGIS, load the CSV tables via `Layer` -> `Add Layer` -> `Add Delimited Text Layer`.
- Join those tables to spatial layers such as TIR or asset WFS layers when shared keys exist.

## Recommended practical workflow

If your goal is to work in GIS:

1. Load **TIR** and Rotterdam **asset services** first.
2. Treat **IMBOR** as the semantic model behind those datasets.
3. Use the IMBOR `.ttl` or `.accdb` files for:
   - field meaning
   - class definitions
   - domain values
   - harmonization and mapping
4. If needed, create a mapping table between Rotterdam service fields and IMBOR concepts.

## Linked Data access

The package also includes SPARQL endpoints for the IMBOR 2025 publications. See the existing file:

- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/SPARQL-Endpoints.md`

These endpoints are useful when you want to inspect or query the model without loading all Turtle files locally.