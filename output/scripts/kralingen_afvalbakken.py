"""Interactieve kaart: Kralingen-Crooswijk met afvalbakken per buurt."""

import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from pathlib import Path

BASE = Path("/Users/ds/Werk/GEOAI test/General data/Data")
OUT  = Path("/Users/ds/Werk/GEOAI test/output")

# ── 1. Laad buurten en filter Kralingen-Crooswijk ────────────────────────────
buurten = gpd.read_file(BASE / "tir_buurten.geojson").set_crs(epsg=28992, allow_override=True)
kralingen = buurten[buurten["GEBDNAAM"] == "Kralingen-Crooswijk"].copy()
print(f"Buurten in Kralingen-Crooswijk: {len(kralingen)}")

# ── 2. Laad afvalbakken en filter op Kralingen ───────────────────────────────
afval = gpd.read_file(BASE / "afvalbak.geojson").set_crs(epsg=28992, allow_override=True)
afval_kralingen = gpd.sjoin(afval, kralingen[["BUURTNAAM", "geometry"]], how="inner", predicate="within")
print(f"Afvalbakken in Kralingen-Crooswijk: {len(afval_kralingen)}")

# ── 3. Reproject naar WGS84 voor Folium ─────────────────────────────────────
kralingen_wgs = kralingen.to_crs(epsg=4326)
afval_wgs = afval_kralingen.to_crs(epsg=4326)

# Centreer kaart op Kralingen
centroid = kralingen_wgs.unary_union.centroid
center = [centroid.y, centroid.x]

# ── 4. Bouw interactieve kaart ───────────────────────────────────────────────
m = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron")

# Kleuren per buurt
KLEUREN = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
]
buurt_namen = sorted(kralingen_wgs["BUURTNAAM"].unique())
kleur_map = {naam: KLEUREN[i % len(KLEUREN)] for i, naam in enumerate(buurt_namen)}

# Buurt polygonen als achtergrond
for _, row in kralingen_wgs.iterrows():
    kleur = kleur_map[row["BUURTNAAM"]]
    folium.GeoJson(
        row["geometry"].__geo_interface__,
        style_function=lambda f, k=kleur: {
            "fillColor": k,
            "color": "#333333",
            "weight": 1.5,
            "fillOpacity": 0.15,
        },
        tooltip=row["BUURTNAAM"],
    ).add_to(m)

# Buurt labels
for _, row in kralingen_wgs.iterrows():
    cx = row.geometry.centroid.x
    cy = row.geometry.centroid.y
    folium.Marker(
        location=[cy, cx],
        icon=folium.DivIcon(
            html=f'<div style="font-size:11px;font-weight:bold;color:#333;'
                 f'white-space:nowrap;text-shadow:1px 1px 2px white">'
                 f'{row["BUURTNAAM"]}</div>',
            icon_size=(140, 20),
            icon_anchor=(70, 10),
        ),
    ).add_to(m)

# Afvalbakken per buurt als MarkerCluster groepen
for buurt_naam in buurt_namen:
    kleur = kleur_map[buurt_naam]
    cluster = MarkerCluster(name=f"Afvalbakken – {buurt_naam}").add_to(m)
    subset = afval_wgs[afval_wgs["BUURTNAAM"] == buurt_naam]
    for _, row in subset.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color=kleur,
            fill=True,
            fill_color=kleur,
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row.get('TYPE', 'Afvalbak')}</b><br>"
                f"Straat: {row.get('STRAAT', '—')}<br>"
                f"Buurt: {buurt_naam}",
                max_width=220,
            ),
        ).add_to(cluster)

# Legenda
counts = afval_wgs.groupby("BUURTNAAM").size()
legend_html = """
<div style="position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
     padding:12px 16px;border-radius:8px;box-shadow:2px 2px 8px rgba(0,0,0,0.3);
     font-family:sans-serif;font-size:13px;min-width:200px">
  <b style="font-size:14px">Kralingen-Crooswijk</b><br>
  <span style="color:#666;font-size:11px">Afvalbakken per buurt</span>
  <hr style="margin:6px 0">
"""
for naam in buurt_namen:
    k = kleur_map[naam]
    n = counts.get(naam, 0)
    legend_html += (
        f'<div style="margin:3px 0">'
        f'<span style="display:inline-block;width:12px;height:12px;'
        f'background:{k};border-radius:50%;margin-right:6px"></span>'
        f'{naam} <b>({n})</b></div>'
    )
legend_html += f"<hr style='margin:6px 0'><b>Totaal: {len(afval_wgs)}</b></div>"

m.get_root().html.add_child(folium.Element(legend_html))
folium.LayerControl(collapsed=False).add_to(m)

# ── 5. Opslaan ───────────────────────────────────────────────────────────────
out = OUT / "kralingen_afvalbakken.html"
m.save(str(out))
print(f"\nOpgeslagen: {out}")
print("\nAfvalbakken per buurt:")
for naam in buurt_namen:
    print(f"  {naam}: {counts.get(naam, 0)}")
