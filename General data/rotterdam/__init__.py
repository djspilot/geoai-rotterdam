"""Rotterdam GeoAI — deep modules behind one flat import surface.

Typical script (10-20 lines):

    import sys
    sys.path.insert(0, "/Users/ds/Werk/GEOAI test/General data")
    from rotterdam import (
        load_layer, filter_to_area, point_map, finalize_map, save_map,
        ROTTERDAM_ZUID_GEBIEDEN,
    )

    gebieden = load_layer("gebieden")
    afval    = load_layer("afvalbak")
    zuid     = filter_to_area(afval, gebieden, gebied_names=ROTTERDAM_ZUID_GEBIEDEN)
    fig, ax  = point_map(zuid, boundary=..., title="Afvalbakken Rotterdam Zuid")
    finalize_map(fig)
    save_map(fig, "afvalbakken_rotterdam_zuid")

Module map:
    paths       — PROJECT_ROOT, DATA, OUTPUT, MAPS_DIR, ...
    vocab       — TIR area lists, ASSET_COLORS, LOCAL_FILES, ARCGIS_LAYERS, STYLE
    loader      — load_rotterdam, load_layer, require_columns, require_paths
    tir         — filter_to_area, count_per_polygon
    cartography — point_map, choropleth, style_map, finalize_map, save_map, validate_map
    arcgis      — fetch_arcgis_layer (paginated REST download)
    geocode     — pdok_geocode_rd, cbs_buurten_rotterdam, nwb_wegvakken

All functions assume EPSG:28992 (RD New) as the canonical working CRS.
"""

from .paths import (
    PROJECT_ROOT, GENERAL_DATA, DATA, OUTPUT, MAPS_DIR, DATA_OUT,
    REPORTS_DIR, SCRIPTS_DIR, CACHE, OUT,
)
from .vocab import (
    RD_NEW, WGS84, ROTTERDAM_CENTER_WGS, ROTTERDAM_CENTER_RD,
    ROTTERDAM_ZUID_GEBIEDEN, ROTTERDAM_NOORD_GEBIEDEN,
    ASSET_COLORS, LOCAL_FILES, ARCGIS_BASE, ARCGIS_LAYERS,
    ASSET_BUURT_FIELD, ASSET_SUBBUURT_FIELD, STYLE, nl_getal,
)
from .loader import (
    load_rotterdam, load_layer,
    require_columns, require_paths, safe_centroids,
)
from .tir import filter_to_area, count_per_polygon
from .cartography import (
    setup_headless_matplotlib,
    style_map, finalize_map, fit_figure_to_data, save_map, validate_map,
    add_scalebar, add_scale_ratio, add_north_arrow, add_area_labels,
    add_pdok_basemap, add_rotterdam_basemap, ROTTERDAM_BASEMAPS,
    place_legend, add_proportional_legend, add_swatch_legend, add_side_panel,
    add_swatch_legend_sidepanel, fit_side_panel,
    point_map, choropleth,
)
from .arcgis import fetch_arcgis_layer
from .geocode import (
    pdok_geocode, pdok_geocode_rd, cbs_buurten_rotterdam, nwb_wegvakken,
)

__all__ = [
    # paths
    "PROJECT_ROOT", "GENERAL_DATA", "DATA", "OUTPUT", "MAPS_DIR", "DATA_OUT",
    "REPORTS_DIR", "SCRIPTS_DIR", "CACHE", "OUT",
    # vocab
    "RD_NEW", "WGS84", "ROTTERDAM_CENTER_WGS", "ROTTERDAM_CENTER_RD",
    "ROTTERDAM_ZUID_GEBIEDEN", "ROTTERDAM_NOORD_GEBIEDEN",
    "ASSET_COLORS", "LOCAL_FILES", "ARCGIS_BASE", "ARCGIS_LAYERS",
    "ASSET_BUURT_FIELD", "ASSET_SUBBUURT_FIELD", "STYLE", "nl_getal",
    # loader
    "load_rotterdam", "load_layer",
    "require_columns", "require_paths", "safe_centroids",
    # tir
    "filter_to_area", "count_per_polygon",
    # cartography
    "setup_headless_matplotlib",
    "style_map", "finalize_map", "fit_figure_to_data", "save_map", "validate_map",
    "add_scalebar", "add_scale_ratio", "add_north_arrow", "add_area_labels",
    "add_pdok_basemap", "add_rotterdam_basemap", "ROTTERDAM_BASEMAPS",
    "place_legend", "add_proportional_legend", "add_swatch_legend", "add_side_panel",
    "add_swatch_legend_sidepanel", "fit_side_panel",
    "point_map", "choropleth",
    # network
    "fetch_arcgis_layer",
    "pdok_geocode", "pdok_geocode_rd", "cbs_buurten_rotterdam", "nwb_wegvakken",
]
