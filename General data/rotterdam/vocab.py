"""Rotterdam domain vocabulary — TIR area definitions, asset endpoints, field names.

Constants live here so a single edit propagates to every script. See CONTEXT.md
for the meaning of TIR, IMBOR, Obsurv, and the gebied/buurt hierarchy.
"""

from __future__ import annotations

from .paths import DATA

RD_NEW = 28992
WGS84 = 4326
ROTTERDAM_CENTER_WGS = (51.9225, 4.47917)
ROTTERDAM_CENTER_RD = (92537, 437503)

ROTTERDAM_ZUID_GEBIEDEN = [
    "Feijenoord", "IJsselmonde", "Charlois", "Hoogvliet",
    "Pernis", "Rozenburg", "Waalhaven-Eemhaven", "Vondelingenplaat",
]
ROTTERDAM_NOORD_GEBIEDEN = [
    "Delfshaven", "Hillegersberg-Schiebroek", "Kralingen-Crooswijk",
    "Nieuw Mathenesse", "Noord", "Overschie", "Prins Alexander",
    "Rivium", "Rotterdam Centrum", "Rotterdam-Noord-West", "Spaanse Polder",
]

ASSET_COLORS = {
    "afvalbak": "#d94841",
    "bomen": "#2d8a4e",
    "lichtpunten": "#f2a900",
    "banken": "#7a5af5",
    "containers": "#3b82f6",
    "wegvakonderdelen": "#666666",
}

LOCAL_FILES = {
    "gemeente": DATA / "tir_gemeente.geojson",
    "gebieden": DATA / "tir_gebieden.geojson",
    "buurten": DATA / "tir_buurten.geojson",
    "subbuurten": DATA / "tir_subbuurten.geojson",
    "subbuurtdelen": DATA / "tir_subbuurtdelen.geojson",
    "afvalbak": DATA / "afvalbak.geojson",
    "bomen_chunks_glob": str(DATA / "bomen_chunks" / "*.geojson"),
    "lichtpunten_stadsdriehoek": DATA / "lichtpunten_stadsdriehoek.geojson",
}

ARCGIS_BASE = "https://diensten.rotterdam.nl/arcgis/rest/services"
ARCGIS_LAYERS = {
    "tir_gemeente":      f"{ARCGIS_BASE}/SB_BI/TIR/MapServer/0",
    "tir_gebieden":      f"{ARCGIS_BASE}/SB_BI/TIR/MapServer/1",
    "tir_buurten":       f"{ARCGIS_BASE}/SB_BI/TIR/MapServer/2",
    "tir_subbuurten":    f"{ARCGIS_BASE}/SB_BI/TIR/MapServer/3",
    "tir_subbuurtdelen": f"{ARCGIS_BASE}/SB_BI/TIR/MapServer/4",
    "bomen":             f"{ARCGIS_BASE}/SB_Infra/Bomen/MapServer/0",
    "afvalbakken":       f"{ARCGIS_BASE}/SB_Infra/Afvalbak/MapServer/0",
    "banken":            f"{ARCGIS_BASE}/SB_Infra/Banken/MapServer/0",
    "lichtpunten":       f"{ARCGIS_BASE}/SB_Infra/LICHTPUNTEN/MapServer/0",
    "wegvakonderdelen":  f"{ARCGIS_BASE}/SB_Infra/Wegvakonderdelen/MapServer/0",
    "containers":        f"{ARCGIS_BASE}/SB_Infra/Container/MapServer/0",
}

# In asset layers (Lichtpunten, Afvalbak, ...) WIJK = TIR buurt, BUURT = TIR subbuurt.
# Filter on WIJK to get a TIR buurt — the names are misleading.
ASSET_BUURT_FIELD = "WIJK"
ASSET_SUBBUURT_FIELD = "BUURT"

STYLE = {
    # Preference order across platforms. cartography._apply_rc() filters this
    # to fonts actually installed, so missing families raise no findfont warnings.
    "font_family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "title_size": 16,
    "title_weight": "bold",
    "title_color": "#1a1a1a",
    "subtitle_size": 10.5,
    "subtitle_color": "#555555",
    "subtitle_weight": "normal",
    "footer_size": 7.5,
    "footer_color": "#888888",
    "boundary_color": "#666666",
    "boundary_width": 0.5,
    "polygon_fill": "#f6f3ee",
    "fig_bg": "#ffffff",
    "ax_bg": "#fafafa",
    "separator_color": "#cccccc",
}


def nl_getal(v, decimalen: int = 0) -> str:
    """Format a number in Dutch/regional notation (invariant 16): thousands
    separated by a **dot**, decimals by a **comma** — e.g. nl_getal(20028) ->
    '20.028', nl_getal(1.5, 1) -> '1,5', nl_getal(1234.5, 1) -> '1.234,5'.

    Use this everywhere a number is shown to the reader (labels, legends, texts)
    instead of `str(v)` or the English default formatting.
    """
    s = f"{float(v):,.{decimalen}f}"          # US style: ',' thousands, '.' decimal
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
