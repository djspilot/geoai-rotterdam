"""Interactieve OpenLayers-kaart van afvalbakken in Rotterdam Zuid.

Genereert een zelfstandig HTML-bestand (OpenLayers via CDN) met OSM-basiskaart,
de Zuid-gebiedsgrenzen en geclusterde afvalbak-punten met klik-popups.
Data wordt naar WGS84 geprojecteerd en ingebed in de pagina, zodat het bestand
ook via file:// werkt (geen aparte GeoJSON-fetch nodig).

Bron: Obsurv via diensten.rotterdam.nl.
"""

import json
import sys

sys.path.insert(0, r"C:\Users\134020\Downloads\geoai-rotterdam-main\General data")

from rotterdam import (
    load_layer, filter_to_area, ROTTERDAM_ZUID_GEBIEDEN, MAPS_DIR, WGS84,
)

POPUP_FIELDS = ["STRAAT", "WIJK", "TYPE", "ID"]

gebieden = load_layer("gebieden")
afval = load_layer("afvalbak")

zuid_grens = gebieden[gebieden["GEBDNAAM"].isin(ROTTERDAM_ZUID_GEBIEDEN)]
zuid = filter_to_area(afval, gebieden, gebied_names=ROTTERDAM_ZUID_GEBIEDEN)

# Alleen relevante popup-velden meenemen (klein houden), reproject naar WGS84.
pts = zuid[[c for c in POPUP_FIELDS if c in zuid.columns] + ["geometry"]].to_crs(WGS84)
grens = zuid_grens[["GEBDNAAM", "geometry"]].to_crs(WGS84)

points_geojson = json.loads(pts.to_json())
boundary_geojson = json.loads(grens.to_json())

# Zwaartepunt voor de begin-view.
c = pts.geometry.union_all().centroid
center_lon, center_lat = c.x, c.y

HTML = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Afvalbakken in Rotterdam Zuid — interactief</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@10.2.1/ol.css">
<style>
  html, body {{ margin: 0; height: 100%; font-family: Arial, Helvetica, sans-serif; }}
  #map {{ position: absolute; top: 0; bottom: 0; left: 0; right: 0; }}
  .panel {{
    position: absolute; top: 12px; left: 12px; z-index: 5;
    background: rgba(255,255,255,0.92); padding: 10px 14px; border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3); max-width: 280px;
  }}
  .panel h1 {{ font-size: 16px; margin: 0 0 4px; }}
  .panel p {{ font-size: 12px; margin: 2px 0; color: #333; }}
  .ol-popup {{
    position: absolute; background: #fff; padding: 10px 12px; border-radius: 6px;
    border: 1px solid #ccc; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    min-width: 160px; font-size: 12px; bottom: 14px; left: -80px;
  }}
  .ol-popup:after {{
    content: ""; position: absolute; top: 100%; left: 50%; margin-left: -8px;
    border: 8px solid transparent; border-top-color: #fff;
  }}
  .ol-popup h3 {{ margin: 0 0 6px; font-size: 13px; }}
  .ol-popup .close {{ position: absolute; top: 4px; right: 8px; cursor: pointer; color: #888; }}
</style>
</head>
<body>
<div id="map"></div>
<div class="panel">
  <h1>Afvalbakken in Rotterdam Zuid</h1>
  <p><b>{n}</b> afvalbakken · klik op een cluster om in te zoomen, op een punt voor details.</p>
  <p style="color:#666">Bron: Obsurv via diensten.rotterdam.nl</p>
</div>
<div id="popup" class="ol-popup" style="display:none">
  <span class="close" id="popup-close">&times;</span>
  <div id="popup-content"></div>
</div>

<script id="points-data" type="application/json">{points}</script>
<script id="boundary-data" type="application/json">{boundary}</script>
<script src="https://cdn.jsdelivr.net/npm/proj4@2.11.0/dist/proj4.js"></script>
<script src="https://cdn.jsdelivr.net/npm/ol@10.2.1/dist/ol.js"></script>
<script>
  // RD New (EPSG:28992) registreren voor de Rotterdamse WMTS-achtergrond.
  proj4.defs('EPSG:28992', '+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 '
    + '+k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel '
    + '+towgs84=565.417,50.3319,465.552,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs');
  ol.proj.proj4.register(proj4);
  const rd = ol.proj.get('EPSG:28992');
  rd.setExtent([-285401.92, 22598.08, 595401.92, 903401.92]);

  const readGeoJSON = id => new ol.format.GeoJSON().readFeatures(
    JSON.parse(document.getElementById(id).textContent),
    {{ dataProjection: 'EPSG:4326', featureProjection: 'EPSG:28992' }}
  );

  // Rotterdamse basiskaart (WMTS, RD/EPSG:28992)
  const wmtsResolutions = [50.800102,25.400051,12.700025,6.350013,3.175006,1.587503,0.793752,0.396876,0.198438,0.099219,0.049609];
  const wmtsMatrixIds = ['0','1','2','3','4','5','6','7','8','9','10'];
  const baseLayer = new ol.layer.Tile({{
    source: new ol.source.WMTS({{
      url: 'https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/Basiskaart_BI_Kleur/MapServer/WMTS/tile/1.0.0/SB_BI_Basiskaart_BI_Kleur/{{Style}}/{{TileMatrixSet}}/{{TileMatrix}}/{{TileRow}}/{{TileCol}}.png',
      layer: 'SB_BI_Basiskaart_BI_Kleur',
      matrixSet: 'default028mm',
      format: 'image/png',
      projection: rd,
      requestEncoding: 'REST',
      style: 'default',
      crossOrigin: 'anonymous',
      tileGrid: new ol.tilegrid.WMTS({{
        origin: [-285401.92, 903401.92],
        resolutions: wmtsResolutions,
        matrixIds: wmtsMatrixIds,
        tileSize: 256,
      }}),
      attributions: '&copy; Gemeente Rotterdam',
    }}),
  }});

  // Gebiedsgrenzen
  const boundaryLayer = new ol.layer.Vector({{
    source: new ol.source.Vector({{ features: readGeoJSON('boundary-data') }}),
    style: new ol.style.Style({{
      stroke: new ol.style.Stroke({{ color: '#444', width: 1.5 }}),
      fill: new ol.style.Fill({{ color: 'rgba(0,0,0,0.03)' }}),
    }}),
  }});

  // Afvalbak-punten, geclusterd
  const pointSource = new ol.source.Vector({{ features: readGeoJSON('points-data') }});
  const clusterSource = new ol.source.Cluster({{ distance: 40, source: pointSource }});

  // Herkenbaar afvalbak-icoon (SVG data-URI) voor losse bakken.
  const binSvg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="30" viewBox="0 0 26 30">'
    + '<rect x="9" y="1" width="8" height="2.6" rx="1.1" fill="#2b2b2b"/>'
    + '<rect x="3.5" y="4" width="19" height="3.2" rx="1.3" fill="#3f3f3f"/>'
    + '<path d="M5.5 7.4 L20.5 7.4 L18.8 26 A2.2 2.2 0 0 1 16.6 28 L9.4 28 A2.2 2.2 0 0 1 7.2 26 Z" '
    + 'fill="#4a4a4a" stroke="#2b2b2b" stroke-width="0.9"/>'
    + '<line x1="10" y1="10.5" x2="10.5" y2="25" stroke="#fff" stroke-width="1.3"/>'
    + '<line x1="13" y1="10.5" x2="13" y2="25" stroke="#fff" stroke-width="1.3"/>'
    + '<line x1="16" y1="10.5" x2="15.5" y2="25" stroke="#fff" stroke-width="1.3"/>'
    + '</svg>';
  const binStyle = new ol.style.Style({{
    image: new ol.style.Icon({{
      src: 'data:image/svg+xml;utf8,' + encodeURIComponent(binSvg),
      anchor: [0.5, 1],
      scale: 0.7,
    }}),
  }});

  const styleCache = {{}};
  const clusterLayer = new ol.layer.Vector({{
    source: clusterSource,
    style: feature => {{
      const size = feature.get('features').length;
      if (size === 1) {{
        return binStyle;
      }}
      let style = styleCache[size];
      if (!style) {{
        const r = Math.min(10 + Math.sqrt(size) * 1.5, 26);
        style = new ol.style.Style({{
          image: new ol.style.Circle({{
            radius: r,
            fill: new ol.style.Fill({{ color: 'rgba(74,74,74,0.85)' }}),
            stroke: new ol.style.Stroke({{ color: '#fff', width: 1.5 }}),
          }}),
          text: new ol.style.Text({{
            text: size.toString(),
            fill: new ol.style.Fill({{ color: '#fff' }}),
            font: 'bold 11px Arial',
          }}),
        }});
        styleCache[size] = style;
      }}
      return style;
    }},
  }});

  const map = new ol.Map({{
    target: 'map',
    layers: [ baseLayer, boundaryLayer, clusterLayer ],
    view: new ol.View({{
      projection: rd,
      center: ol.proj.fromLonLat([{lon}, {lat}], rd),
      resolution: wmtsResolutions[3],
      maxResolution: wmtsResolutions[0],
      minResolution: wmtsResolutions[wmtsResolutions.length - 1],
    }}),
  }});

  // Begin-view: pas op de extent zodra de mapgrootte bekend is (na 1e render).
  map.once('rendercomplete', function () {{
    map.getView().fit(boundaryLayer.getSource().getExtent(), {{ padding: [30, 30, 30, 30] }});
  }});

  window.olMap = map;  // handig voor console/debug

  // Popup
  const popup = document.getElementById('popup');
  const content = document.getElementById('popup-content');
  const overlay = new ol.Overlay({{ element: popup, autoPan: {{ animation: {{ duration: 200 }} }} }});
  map.addOverlay(overlay);
  document.getElementById('popup-close').onclick = () => {{ popup.style.display = 'none'; return false; }};

  map.on('click', evt => {{
    const feature = map.forEachFeatureAtPixel(evt.pixel, f => f, {{ layerFilter: l => l === clusterLayer }});
    popup.style.display = 'none';
    if (!feature) return;
    const members = feature.get('features');
    if (members.length > 1) {{
      // Cluster: inzoomen op de omvattende extent.
      const ext = ol.extent.createEmpty();
      members.forEach(m => ol.extent.extend(ext, m.getGeometry().getExtent()));
      map.getView().fit(ext, {{ duration: 350, padding: [60,60,60,60], maxZoom: 18 }});
      return;
    }}
    const p = members[0].getProperties();
    content.innerHTML = '<h3>' + (p.STRAAT || 'Afvalbak') + '</h3>'
      + '<div>Wijk: ' + (p.WIJK || '–') + '</div>'
      + '<div>Type: ' + (p.TYPE || '–') + '</div>'
      + '<div style="color:#888">ID: ' + (p.ID || '–') + '</div>';
    overlay.setPosition(members[0].getGeometry().getCoordinates());
    popup.style.display = 'block';
  }});

  map.on('pointermove', evt => {{
    const hit = map.hasFeatureAtPixel(evt.pixel, {{ layerFilter: l => l === clusterLayer }});
    map.getTargetElement().style.cursor = hit ? 'pointer' : '';
  }});
</script>
</body>
</html>
"""

html = HTML.format(
    n=len(zuid),
    points=json.dumps(points_geojson),
    boundary=json.dumps(boundary_geojson),
    lon=center_lon,
    lat=center_lat,
)

out = MAPS_DIR / "kaart_rotterdam_zuid_openlayers.html"
out.write_text(html, encoding="utf-8")
print(f"Afvalbakken in Zuid: {len(zuid)}")
print(f"SAVED: {out}")
