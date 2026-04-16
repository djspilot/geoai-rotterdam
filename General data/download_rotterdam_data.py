"""Download Rotterdam TIR and selected asset layers to local GeoJSON files.

This script uses ArcGIS REST query endpoints instead of WFS because those
endpoints respond more reliably in this environment.
"""

from __future__ import annotations

import json
import math
import ssl
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


OUTPUT_DIR = Path("/Users/ds/Werk/GEOAI test/Data")
BATCH_SIZE = 1000

LAYERS = [
    {
        "name": "tir_gemeente",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/0",
    },
    {
        "name": "tir_gebieden",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/1",
    },
    {
        "name": "tir_buurten",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/2",
    },
    {
        "name": "tir_subbuurten",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/3",
    },
    {
        "name": "tir_subbuurtdelen",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_BI/TIR/MapServer/4",
    },
    {
        "name": "bomen",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Bomen/MapServer/0",
    },
    {
        "name": "afvalbak",
        "url": "https://diensten.rotterdam.nl/arcgis/rest/services/SB_Infra/Afvalbak/MapServer/0",
    },
]


SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def fetch_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params, doseq=True)
    full_url = f"{url}?{query}"
    with urlopen(full_url, context=SSL_CONTEXT, timeout=60) as response:
        return json.load(response)


def fetch_text(url: str, params: dict[str, Any]) -> str:
    query = urlencode(params, doseq=True)
    full_url = f"{url}?{query}"
    with urlopen(full_url, context=SSL_CONTEXT, timeout=60) as response:
        return response.read().decode("utf-8")


def get_object_ids(layer_url: str) -> list[int]:
    payload = fetch_json(
        f"{layer_url}/query",
        {
            "where": "1=1",
            "returnIdsOnly": "true",
            "f": "json",
        },
    )
    object_ids = payload.get("objectIds") or []
    return sorted(int(object_id) for object_id in object_ids)


def get_feature_count(layer_url: str) -> int:
    payload = fetch_json(
        f"{layer_url}/query",
        {
            "where": "1=1",
            "returnCountOnly": "true",
            "f": "json",
        },
    )
    return int(payload.get("count") or 0)


def get_metadata(layer_url: str) -> dict[str, Any]:
    return fetch_json(layer_url, {"f": "json"})


def fetch_geojson_batch(layer_url: str, result_offset: int, result_record_count: int, out_sr: int = 28992) -> dict[str, Any]:
    text = fetch_text(
        f"{layer_url}/query",
        {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": str(out_sr),
            "resultOffset": str(result_offset),
            "resultRecordCount": str(result_record_count),
            "f": "geojson",
        },
    )
    return json.loads(text)


def download_layer(layer: dict[str, str]) -> Path:
    layer_name = layer["name"]
    layer_url = layer["url"]
    metadata = get_metadata(layer_url)
    feature_count = get_feature_count(layer_url)
    output_path = OUTPUT_DIR / f"{layer_name}.geojson"

    if feature_count == 0:
        empty_collection = {"type": "FeatureCollection", "features": []}
        output_path.write_text(json.dumps(empty_collection, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    feature_collection: dict[str, Any] = {"type": "FeatureCollection", "features": []}
    if "crs" in metadata:
        feature_collection["crs"] = metadata["crs"]

    total_batches = math.ceil(feature_count / BATCH_SIZE)
    for index in range(total_batches):
        start = index * BATCH_SIZE
        batch_size = min(BATCH_SIZE, feature_count - start)
        print(f"Downloading {layer_name}: batch {index + 1}/{total_batches} ({batch_size} features)")
        batch_geojson = fetch_geojson_batch(layer_url, start, batch_size)
        feature_collection["features"].extend(batch_geojson.get("features", []))

    output_path.write_text(json.dumps(feature_collection, ensure_ascii=False), encoding="utf-8")
    return output_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for layer in LAYERS:
        print(f"Starting {layer['name']}")
        path = download_layer(layer)
        downloaded.append(path)
        print(f"Saved {path}")

    print("Finished downloads:")
    for path in downloaded:
        print(path)


if __name__ == "__main__":
    main()