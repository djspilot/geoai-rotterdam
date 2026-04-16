"""PyQGIS script to load Rotterdam TIR and asset WFS layers.

Run this in the QGIS Python Console or from the Script Editor.

What it does:
- fetches WFS GetCapabilities for each configured service
- discovers the available feature types automatically
- adds those layers to the current QGIS project
- groups layers under Rotterdam / TIR and Rotterdam / Assets

Tested for syntax only outside QGIS. Execution requires QGIS.
"""

from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from qgis.core import QgsLayerTreeGroup, QgsProject, QgsVectorLayer


SERVICES = {
    "TIR": {
        "group": "TIR",
        "endpoint": "https://diensten.rotterdam.nl/arcgis/services/SB_BI/TIR/MapServer/WFSServer",
        "enabled": True,
    },
    "Bomen": {
        "group": "Assets",
        "endpoint": "https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Bomen/MapServer/WFSServer",
        "enabled": True,
    },
    "Afvalbak": {
        "group": "Assets",
        "endpoint": "https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Afvalbak/MapServer/WFSServer",
        "enabled": True,
    },
    "Banken": {
        "group": "Assets",
        "endpoint": "https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Banken/MapServer/WFSServer",
        "enabled": False,
    },
    "Lichtpunten": {
        "group": "Assets",
        "endpoint": "https://diensten.rotterdam.nl/arcgis/services/SB_Infra/LICHTPUNTEN/MapServer/WFSServer",
        "enabled": False,
    },
    "Wegvakonderdelen": {
        "group": "Assets",
        "endpoint": "https://diensten.rotterdam.nl/arcgis/services/SB_Infra/Wegvakonderdelen/MapServer/WFSServer",
        "enabled": False,
    },
}

DEFAULT_CRS = "EPSG:28992"
ROOT_GROUP_NAME = "Rotterdam"


def fetch_xml(url, params=None):
    query = urlencode(params or {})
    full_url = f"{url}?{query}" if query else url
    with urlopen(full_url, timeout=30) as response:
        return response.read()


def discover_feature_types(endpoint):
    content = fetch_xml(
        endpoint,
        {
            "service": "WFS",
            "request": "GetCapabilities",
            "version": "2.0.0",
        },
    )
    root = ET.fromstring(content)
    namespaces = {
        "wfs": "http://www.opengis.net/wfs/2.0",
        "ows": "http://www.opengis.net/ows/1.1",
    }

    feature_types = []
    for node in root.findall(".//wfs:FeatureType", namespaces):
        name_node = node.find("wfs:Name", namespaces)
        title_node = node.find("wfs:Title", namespaces)
        if name_node is None or not name_node.text:
            continue
        feature_types.append(
            {
                "name": name_node.text.strip(),
                "title": title_node.text.strip() if title_node is not None and title_node.text else name_node.text.strip(),
            }
        )
    return feature_types


def ensure_group(parent, name):
    existing = parent.findGroup(name)
    if existing:
        return existing
    return parent.addGroup(name)


def build_wfs_uri(endpoint, typename, crs=DEFAULT_CRS):
    parts = [
        f"url='{endpoint}'",
        f"typename='{typename}'",
        "version='2.0.0'",
        f"srsname='{crs}'",
        "restrictToRequestBBOX='1'",
        "pagingEnabled='true'",
        "preferCoordinatesForWfsT11='false'",
    ]
    return " ".join(parts)


def add_wfs_layer(endpoint, feature_type, target_group):
    uri = build_wfs_uri(endpoint, feature_type["name"])
    layer = QgsVectorLayer(uri, feature_type["title"], "WFS")
    if not layer.isValid():
        print(f"Failed to load {feature_type['title']} from {endpoint}")
        return None

    project = QgsProject.instance()
    project.addMapLayer(layer, False)
    target_group.addLayer(layer)
    print(f"Loaded: {feature_type['title']}")
    return layer


def load_services():
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    rotterdam_group = ensure_group(root, ROOT_GROUP_NAME)
    group_cache = {}

    loaded_count = 0
    failed_services = []

    for service_name, service in SERVICES.items():
        if not service.get("enabled", True):
            continue

        group_name = service["group"]
        target_group = group_cache.get(group_name)
        if target_group is None:
            target_group = ensure_group(rotterdam_group, group_name)
            group_cache[group_name] = target_group

        print(f"Discovering feature types for {service_name}...")
        try:
            feature_types = discover_feature_types(service["endpoint"])
        except Exception as exc:
            failed_services.append((service_name, str(exc)))
            print(f"Failed to read capabilities for {service_name}: {exc}")
            continue

        if not feature_types:
            failed_services.append((service_name, "No feature types returned"))
            print(f"No feature types found for {service_name}")
            continue

        for feature_type in feature_types:
            layer = add_wfs_layer(service["endpoint"], feature_type, target_group)
            if layer is not None:
                loaded_count += 1

    print(f"Finished. Loaded {loaded_count} layers.")
    if failed_services:
        print("Services with issues:")
        for service_name, reason in failed_services:
            print(f"- {service_name}: {reason}")


load_services()