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
    "verkeersborden":    f"{ARCGIS_BASE}/SB_Infra/Verkeersborden/MapServer/0",
    # Overige openbare-ruimte-assets (SB_Infra). Geometrie in commentaar: punt/lijn/vlak.
    # Test-/duplicaatservices bewust weggelaten (Boringen_test, Sondering_BOR3,
    # TestDiensten, Testprod, Testproddiensten).
    "beelden":                     f"{ARCGIS_BASE}/SB_Infra/Beelden/MapServer/0",   # punt
    "beschoeiingen":               f"{ARCGIS_BASE}/SB_Infra/Beschoeiingen/MapServer/0",   # lijn
    "bollards":                    f"{ARCGIS_BASE}/SB_Infra/Bollards/MapServer/0",   # punt
    "boringen":                    f"{ARCGIS_BASE}/SB_Infra/Boringen/MapServer/0",   # punt
    "brugwachtersverblijven":      f"{ARCGIS_BASE}/SB_Infra/BrugwachtersVerblijven/MapServer/0",   # punt
    "civiele_kunstwerken":         f"{ARCGIS_BASE}/SB_Infra/Civiele_Kunstwerken/MapServer/0",   # vlak
    "civiele_kunstwerken_verkeer": f"{ARCGIS_BASE}/SB_Infra/Civiele_kunstwerken_verkeer/MapServer/0",   # vlak
    "detectors":                   f"{ARCGIS_BASE}/SB_Infra/Detectors/MapServer/0",   # punt
    "duikers":                     f"{ARCGIS_BASE}/SB_Infra/Duikers/MapServer/0",   # lijn
    "electrakast":                 f"{ARCGIS_BASE}/SB_Infra/Electrakast/MapServer/0",   # punt
    "evenementkasten":             f"{ARCGIS_BASE}/SB_Infra/Evenementkasten/MapServer/0",   # punt
    "faunavoorzieningen":          f"{ARCGIS_BASE}/SB_Infra/Faunavoorzieningen/MapServer/0",   # punt
    "fietsbeugelsklemmen":         f"{ARCGIS_BASE}/SB_Infra/FietsBeugelsKlemmen/MapServer/0",   # punt
    "fietsenstalling":             f"{ARCGIS_BASE}/SB_Infra/Fietsenstalling/MapServer/0",   # lijn
    "fietshekken":                 f"{ARCGIS_BASE}/SB_Infra/Fietshekken/MapServer/0",   # lijn
    "fietstrommel":                f"{ARCGIS_BASE}/SB_Infra/FietsTrommel/MapServer/0",   # punt
    "fontein":                     f"{ARCGIS_BASE}/SB_Infra/Fontein/MapServer/0",   # punt
    "geleiderail":                 f"{ARCGIS_BASE}/SB_Infra/Geleiderail/MapServer/0",   # lijn
    "glooiingen":                  f"{ARCGIS_BASE}/SB_Infra/Glooiingen/MapServer/0",   # vlak
    "greppels":                    f"{ARCGIS_BASE}/SB_Infra/Greppels/MapServer/0",   # vlak
    "groeiplaatsverbeteringen":    f"{ARCGIS_BASE}/SB_Infra/Groeiplaatsverbeteringen/MapServer/0",   # vlak
    "groen_punten":                f"{ARCGIS_BASE}/SB_Infra/Groen_punten/MapServer/0",   # punt
    "groen_vlakken":               f"{ARCGIS_BASE}/SB_Infra/Groen_vlakken/MapServer/0",   # vlak
    "hakhout_griend":              f"{ARCGIS_BASE}/SB_Infra/Hakhout_griend/MapServer/0",   # vlak
    "havenbekkens":                f"{ARCGIS_BASE}/SB_Infra/Havenbekkens/MapServer/0",   # vlak
    "hekken":                      f"{ARCGIS_BASE}/SB_Infra/Hekken/MapServer/0",   # lijn
    "hondenkaart":                 f"{ARCGIS_BASE}/SB_Infra/Hondenkaart/MapServer/0",   # vlak
    "hoogtebegrenzers":            f"{ARCGIS_BASE}/SB_Infra/Hoogtebegrenzers/MapServer/0",   # lijn
    "informatiebord":              f"{ARCGIS_BASE}/SB_Infra/Informatiebord/MapServer/0",   # punt
    "kolken":                      f"{ARCGIS_BASE}/SB_Infra/Kolken/MapServer/0",   # punt
    "laadpalen":                   f"{ARCGIS_BASE}/SB_Infra/Laadpalen/MapServer/0",   # punt
    "meerpalen":                   f"{ARCGIS_BASE}/SB_Infra/Meerpalen/MapServer/0",   # punt
    "moerasvegetatie":             f"{ARCGIS_BASE}/SB_Infra/Moerasvegetatie/MapServer/0",   # vlak
    "monumenten":                  f"{ARCGIS_BASE}/SB_Infra/Monumenten/MapServer/0",   # punt
    "murenplantenbak":             f"{ARCGIS_BASE}/SB_Infra/MurenPlantenbak/MapServer/0",   # vlak
    "objecten_eigendom":           f"{ARCGIS_BASE}/SB_Infra/Objecten_Eigendom/MapServer/0",   # vlak
    "palen":                       f"{ARCGIS_BASE}/SB_Infra/Palen/MapServer/0",   # punt
    "parkeerautomaat":             f"{ARCGIS_BASE}/SB_Infra/Parkeerautomaat/MapServer/0",   # punt
    "parkeervoorzieningen":        f"{ARCGIS_BASE}/SB_Infra/Parkeervoorzieningen/MapServer/0",   # punt
    "pergola":                     f"{ARCGIS_BASE}/SB_Infra/Pergola/MapServer/0",   # punt
    "sondering":                   f"{ARCGIS_BASE}/SB_Infra/Sondering/MapServer/0",   # punt
    "speelondergronden":           f"{ARCGIS_BASE}/SB_Infra/Speelondergronden/MapServer/0",   # vlak
    "speelplekken":                f"{ARCGIS_BASE}/SB_Infra/Speelplekken/MapServer/0",   # vlak
    "speeltoestellen":             f"{ARCGIS_BASE}/SB_Infra/Speeltoestellen/MapServer/0",   # punt
    "stolpersteine":               f"{ARCGIS_BASE}/SB_Infra/Stolpersteine/MapServer/0",   # punt
    "straatgoot":                  f"{ARCGIS_BASE}/SB_Infra/Straatgoot/MapServer/0",   # lijn
    "stranddouches":               f"{ARCGIS_BASE}/SB_Infra/Stranddouches/MapServer/0",   # punt
    "toilet":                      f"{ARCGIS_BASE}/SB_Infra/Toilet/MapServer/0",   # punt
    "tvm_actueel_punten":          f"{ARCGIS_BASE}/SB_Infra/TVM_Actueel_punten/MapServer/0",   # punt
    "tvm_vlakken":                 f"{ARCGIS_BASE}/SB_Infra/TVM_vlakken/MapServer/0",   # vlak
    "verdeelkasten":               f"{ARCGIS_BASE}/SB_Infra/Verdeelkasten/MapServer/0",   # punt
    "watergangen":                 f"{ARCGIS_BASE}/SB_Infra/Watergangen/MapServer/0",   # vlak
    "watertappunten":              f"{ARCGIS_BASE}/SB_Infra/Watertappunten/MapServer/0",   # punt
    "wegmarkering_vlakken":        f"{ARCGIS_BASE}/SB_Infra/Wegmarkering_Vlakken/MapServer/0",   # vlak
    "wegmarkeringen_lijnen":       f"{ARCGIS_BASE}/SB_Infra/Wegmarkeringen_Lijnen/MapServer/0",   # lijn
    "wegmarkeringen_punten":       f"{ARCGIS_BASE}/SB_Infra/Wegmarkeringen_Punten/MapServer/0",   # punt
    "wildrooster":                 f"{ARCGIS_BASE}/SB_Infra/Wildrooster/MapServer/0",   # punt
}

# In asset layers (Lichtpunten, Afvalbak, ...) WIJK = TIR buurt, BUURT = TIR subbuurt.
# Filter on WIJK to get a TIR buurt — the names are misleading.
ASSET_BUURT_FIELD = "WIJK"
ASSET_SUBBUURT_FIELD = "BUURT"

STYLE = {
    # Preference order across platforms. cartography._apply_rc() filters this
    # to fonts actually installed, so missing families raise no findfont warnings.
    "font_family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    # Titelhiërarchie (skill-invariant "Titelhiërarchie"): hoofdtitel altijd vet en
    # groter dan de subtitel (die dus nooit vet is); bij deelkaarten is de
    # overkoepelende hoofdtitel (suptitle) groter dan de deelkaart-titels (title).
    "suptitle_size": 19,        # overkoepelende hoofdtitel bij meerdere deelkaarten
    "suptitle_weight": "bold",
    "title_size": 16,           # (deelkaart-)titel / hoofdtitel van een enkele kaart
    "title_weight": "bold",
    "title_color": "#1a1a1a",
    "subtitle_size": 10.5,      # kleiner dan de titel; nooit vet
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
