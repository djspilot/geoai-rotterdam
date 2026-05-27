"""ArcGIS REST paginated download for the Rotterdam diensten.* services.

Rotterdam's TLS chain occasionally trips Python's default verification — this
module centralises the SSL workaround so individual scripts don't reinvent it.
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from urllib.parse import urlencode

from .vocab import RD_NEW


def _ssl_context(verify: bool = False) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_arcgis_layer(
    layer_url: str,
    where: str = "1=1",
    out_fields: str = "*",
    out_sr: int = RD_NEW,
    batch_size: int = 1000,
    verify_ssl: bool = False,
) -> dict:
    """Download a full ArcGIS REST layer as one GeoJSON FeatureCollection."""
    ctx = _ssl_context(verify_ssl)

    def _get(params: dict) -> dict:
        url = f"{layer_url}/query?{urlencode(params)}"
        with urllib.request.urlopen(url, context=ctx, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))

    count = _get({"where": where, "returnCountOnly": "true", "f": "json"})["count"]
    features: list = []
    offset = 0
    while offset < count:
        chunk = _get({
            "where": where, "outFields": out_fields,
            "returnGeometry": "true", "outSR": str(out_sr),
            "resultOffset": str(offset),
            "resultRecordCount": str(batch_size),
            "f": "geojson",
        })
        features.extend(chunk.get("features", []))
        offset += batch_size
        time.sleep(0.1)
    return {"type": "FeatureCollection", "features": features}
