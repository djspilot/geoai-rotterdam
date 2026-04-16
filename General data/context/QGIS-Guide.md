# QGIS Guide

## Purpose

This guide explains how to use the files and services in this workspace from a **QGIS** workflow.

The short version is:

- use **TIR** and **asset WFS services** as your actual GIS layers
- use **IMBOR 2025** as the data model and semantic reference
- treat the `.ttl` files and `.accdb` file as supporting model resources, not as ready-to-map layers

## What in this workspace can be loaded directly in QGIS

### Directly usable in QGIS

- Rotterdam **TIR WFS service**
- Rotterdam **asset WFS services**
- exported CSV tables from the Access database
- derived GeoJSON, CSV, or GeoPackage created from other sources

### Not directly useful as map layers without conversion

- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/*.ttl`
- `IMBOR-2025/IMBOR2025.accdb`

The Turtle files are RDF/OWL Linked Data files. QGIS does not treat them as standard vector layers.

## Recommended QGIS workflow

1. Load the **TIR** layers first.
2. Load one or more **asset WFS** layers.
3. Inspect their fields and geometry types.
4. Use the IMBOR files to interpret field meaning, object classes, and domain values.
5. If needed, build lookup tables or joins from IMBOR-derived exports.

## Step 1: Add TIR to QGIS

### Best option: use WFS

Use this endpoint:

- `https://diensten.rotterdam.nl/arcgis/services/SB_BI/TIR/MapServer/WFSServer?request=GetCapabilities&service=WFS`

### In QGIS

1. Open QGIS.
2. Go to `Layer` -> `Data Source Manager`.
3. Select `WFS / OGC API - Features`.
4. Click `New`.
5. Give the connection a name, for example `Rotterdam TIR`.
6. Paste the WFS URL.
7. Click `OK`.
8. Click `Connect`.
9. Select the layers you want.
10. Click `Add`.

### Expected TIR layers

Depending on service exposure, you should see layers related to:

- gemeente
- gebieden
- buurten
- subbuurten
- subbuurtdelen

### Practical advice

- Start with only one or two layers to confirm performance.
- Save the project immediately after successful connection.
- If layer names are cryptic, rename them in the QGIS layer panel.

## Step 2: Add asset layers to QGIS

### Available WFS endpoints

#### Bomen

- `https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Bomen/MapServer/WFSServer?request=GetCapabilities&service=WFS`

#### Afvalbakken

- `https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Afvalbak/MapServer/WFSServer?request=GetCapabilities&service=WFS`

#### Banken

- `https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Banken/MapServer/WFSServer?request=GetCapabilities&service=WFS`

#### Lichtpunten

- `https://diensten.rotterdam.nl/arcgis/services/SB_Infra/LICHTPUNTEN/MapServer/WFSServer?request=GetCapabilities&service=WFS`

#### Wegvakonderdelen

- `https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Wegvakonderdelen/MapServer/WFSServer?request=GetCapabilities&service=WFS`

### In QGIS

For each endpoint:

1. Add a new WFS connection.
2. Paste the service URL.
3. Connect.
4. Add the layer.

If you want a cleaner setup, create separate named connections such as:

- `Rotterdam Assets - Bomen`
- `Rotterdam Assets - Afvalbak`
- `Rotterdam Assets - Banken`
- `Rotterdam Assets - Lichtpunten`
- `Rotterdam Assets - Wegvakonderdelen`

## Step 3: Inspect CRS, geometry, and fields

After loading a layer in QGIS:

1. Right-click the layer.
2. Open `Properties`.
3. Check:
   - `Source`
   - geometry type
   - CRS
   - field list
4. Open the attribute table.
5. Identify likely keys, codes, and classification fields.

### What to look for

- object identifiers
- area or neighborhood codes
- object type fields
- status fields
- domain-coded attributes that may correspond to IMBOR domain values

## Step 4: Use TIR as the reference geography

TIR is useful as a boundary and reference framework.

Typical QGIS operations:

- style assets by neighborhood or area
- clip assets to a territory
- count assets per area
- spatially join assets to TIR polygons

### Example: assign each tree to a neighborhood

1. Load `Bomen`.
2. Load the TIR neighborhood layer.
3. Open `Processing Toolbox`.
4. Run `Join attributes by location`.
5. Use trees as the input layer.
6. Use TIR neighborhoods as the join layer.
7. Choose the `within` or `intersects` predicate based on geometry behavior.
8. Save the result as GeoPackage.

## Step 5: Use IMBOR as the semantic reference

The IMBOR files in this workspace describe the model behind the data.

### Relevant files

- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/imbor2025-kern.ttl`
- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/imbor2025-vocabulaire.ttl`
- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/imbor2025-domeinwaarden.ttl`
- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/imbor2025-addendum-geometrie.ttl`
- `IMBOR-2025/IMBOR-2025 (LinkedData zipfile)/SPARQL-Endpoints.md`

### What they are useful for in QGIS projects

- understanding object class meaning
- interpreting coded values
- documenting field definitions
- building lookup tables for attribute values
- mapping local service fields to IMBOR concepts

### What they are not

- they are not plug-and-play vector layers
- they are not a ready-made municipal asset database for direct display in QGIS

## Step 6: Work with the Access file on macOS

The file `IMBOR-2025/IMBOR2025.accdb` is a Microsoft Access database.

On macOS, the realistic QGIS workflow is usually indirect:

1. Open the file on a Windows machine with Microsoft Access, or another tool that can read `.accdb`.
2. Export relevant tables to CSV.
3. In QGIS, go to `Layer` -> `Add Layer` -> `Add Delimited Text Layer`.
4. Load the CSV.
5. If there is no geometry, use it as a non-spatial lookup table.
6. Join it to spatial layers using common keys.

### Good use cases for exported IMBOR tables

- field code descriptions
- domain value lookups
- class definitions
- classification support for styling and labeling

## Step 7: Save results in GeoPackage

For practical work in QGIS, do not depend on live WFS layers for everything.

Recommended pattern:

1. Load the WFS layer.
2. Right-click the layer.
3. Choose `Export` -> `Save Features As...`.
4. Save as `GeoPackage`.
5. Use the local GeoPackage for analysis, joins, styling, and backups.

This avoids slow repeated network requests and gives you stable project inputs.

## Suggested project structure in QGIS

Use a GeoPackage such as `rotterdam_assets.gpkg` with layers like:

- `tir_gemeente`
- `tir_gebieden`
- `tir_buurten`
- `assets_bomen`
- `assets_afvalbak`
- `assets_banken`
- `assets_lichtpunten`
- `assets_wegvakonderdelen`
- `lookup_imbor_domainvalues`

## Styling advice

### TIR

- use muted polygon fills
- show labels only at the scale where they remain readable
- avoid showing every territorial level at once

### Assets

- style by object type or status if available
- use scale-dependent visibility
- cluster dense point layers if the map becomes unreadable

## Troubleshooting in QGIS

### WFS connection does not list layers

Possible causes:

- endpoint temporarily unavailable
- service blocks some client behavior
- TLS, proxy, or network issue

What to try:

1. Open the GetCapabilities URL in a browser.
2. Confirm it returns XML.
3. Recreate the QGIS connection.
4. Try another WFS version if QGIS exposes that option.

### Layer loads slowly

What to do:

1. Limit the number of layers loaded at once.
2. Export the layer to GeoPackage.
3. Use local copies for analysis.

### Attributes are unclear

What to do:

1. Compare field names against IMBOR concepts.
2. Use the IMBOR vocabulary and domain values as reference.
3. Build a small lookup CSV manually if needed.

### The Turtle files do not open as GIS layers

That is expected. They are semantic model files, not standard vector formats.

## Practical first session in QGIS

If you want a reliable first run, do this:

1. Add TIR via WFS.
2. Add `Bomen` via WFS.
3. Export both to GeoPackage.
4. Run a spatial join from trees to neighborhoods.
5. Make a choropleth or categorized style.
6. Use IMBOR files only to interpret fields and categories.

## When to use SPARQL instead of QGIS

Use the IMBOR SPARQL endpoints when you need to:

- search for class definitions
- inspect domain values
- understand model relationships
- check terminology across model modules

Use QGIS when you need to:

- map features
- perform spatial joins
- aggregate by area
- style and export layers

## Bottom line

For QGIS, the usable geodata in this workspace context comes from the **Rotterdam WFS services**.

The IMBOR resources are best used as:

- a schema reference
- a terminology source
- a domain-value reference
- a basis for mapping and documentation