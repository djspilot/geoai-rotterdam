"""Download a small local Rotterdam geodata cache for mapping scripts."""

from __future__ import annotations

import json
import ssl
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


OUT = Path(__file__).resolve().parent / "data_cache"
BASE = "https://diensten.rotterdam.nl/arcgis/rest/services"

LAYERS = {
    "tir_gebieden": f"{BASE}/SB_BI/TIR/MapServer/1",
    "afvalbak": f"{BASE}/SB_Infra/Afvalbak/MapServer/0",
    "bomen": f"{BASE}/SB_Infra/Bomen/FeatureServer/0",
}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def fetch_json(url: str) -> dict:
    with urlopen(url, context=CTX, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def feature_count(layer_url: str) -> int:
    params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    data = fetch_json(f"{layer_url}/query?{urlencode(params)}")
    return int(data["count"])


def fetch_geojson_page(layer_url: str, offset: int, batch_size: int) -> dict:
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "28992",
        "resultOffset": str(offset),
        "resultRecordCount": str(batch_size),
        "f": "geojson",
    }
    return fetch_json(f"{layer_url}/query?{urlencode(params)}")


def download_layer(name: str, layer_url: str, batch_size: int = 1000) -> Path:
    total = feature_count(layer_url)
    print(f"{name}: {total} features")
    features = []
    for offset in range(0, total, batch_size):
        page = fetch_geojson_page(layer_url, offset, batch_size)
        batch = page.get("features", [])
        features.extend(batch)
        print(f"  fetched {min(offset + batch_size, total)}/{total}")
        time.sleep(0.15)
    geojson = {"type": "FeatureCollection", "features": features}
    OUT.mkdir(exist_ok=True)
    out_path = OUT / f"{name}.geojson"
    out_path.write_text(json.dumps(geojson), encoding="utf-8")
    return out_path


def main():
    for name, url in LAYERS.items():
        path = download_layer(name, url)
        print(f"saved: {path}")


if __name__ == "__main__":
    main()
