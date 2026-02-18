
import math
import time
import logging
import httpx
from typing import Optional
from config import HTTP_TIMEOUT, CACHE_TTL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server-side TTL cache
# ---------------------------------------------------------------------------
_api_cache: dict = {}  # key -> {"data": ..., "ts": float}

def cache_get(key: str):
    """Return cached data if still fresh, else None."""
    entry = _api_cache.get(key)
    if entry and (time.time() - entry["ts"] < CACHE_TTL):
        return entry["data"]
    return None

def cache_set(key: str, data):
    _api_cache[key] = {"data": data, "ts": time.time()}

# ---------------------------------------------------------------------------
# HTTP Helpers
# ---------------------------------------------------------------------------
async def fetch_json(client: httpx.AsyncClient, url: str, params: Optional[dict] = None):
    """Fetch JSON with timeout and server-side caching; returns None on failure."""
    cache_key = f"{url}|{str(sorted(params.items()) if params else '')}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        resp = await client.get(url, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        cache_set(cache_key, data)
        return data
    except Exception as e:
        logger.warning(f"fetch_json FAILED: {url} — {type(e).__name__}: {e}")
        return None

async def fetch_text(client: httpx.AsyncClient, url: str, params: Optional[dict] = None):
    """Fetch raw text with timeout; returns None on failure."""
    try:
        resp = await client.get(url, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"fetch_text FAILED: {url} — {type(e).__name__}: {e}")
        return None


def haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))

def simplify_coordinates(coords: list, max_points: int = 200) -> list:
    """Reduce coordinates to max_points by uniform sampling."""
    if len(coords) <= max_points:
        return coords
    step = len(coords) / max_points
    simplified = [coords[int(i * step)] for i in range(max_points)]
    # Ensure ring closure
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return simplified

def simplify_geojson(geojson: dict) -> dict:
    """Reduce polygon complexity if very large."""
    if not geojson or "features" not in geojson:
        return geojson
    for feature in geojson.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") == "Polygon":
            geom["coordinates"] = [
                simplify_coordinates(ring) for ring in geom["coordinates"]
            ]
        elif geom.get("type") == "MultiPolygon":
            geom["coordinates"] = [
                [simplify_coordinates(ring) for ring in poly]
                for poly in geom["coordinates"]
            ]
    return geojson

def create_circle_polygon(lat, lon, radius_km, num_points=64):
    """Create a polygon approximating a circle on the sphere."""
    coords = []
    for i in range(num_points + 1):
        angle = (2 * math.pi * i) / num_points
        dlat = radius_km / 111.32 * math.cos(angle)
        dlon = radius_km / (111.32 * math.cos(math.radians(lat))) * math.sin(angle)
        coords.append([round(lon + dlon, 6), round(lat + dlat, 6)])
    return coords

def generate_wind_radii_geojson(storm):
    """
    Generate wind field GeoJSON polygons from storm data.
    Uses reported wind radii (34kt, 50kt, 64kt) when available,
    or estimates from intensity for visualization.
    """
    center_lat = storm.get("lat", 0)
    center_lon = storm.get("lon", 0)
    intensity_str = str(storm.get("intensity", "0"))

    try:
        intensity_kt = int(intensity_str.replace("KT", "").replace("kt", "").strip())
    except (ValueError, TypeError):
        intensity_kt = 0

    features = []

    # Define wind zones based on intensity
    zones = []
    if intensity_kt >= 64:
        zones.append({"radius_nm": 30, "label": "Hurricane Force (≥64kt)", "severity": "severe", "color": "#dc2626"})
        zones.append({"radius_nm": 80, "label": "Storm Force (50-63kt)", "severity": "moderate", "color": "#f97316"})
        zones.append({"radius_nm": 150, "label": "Gale Force (34-49kt)", "severity": "low", "color": "#22c55e"})
    elif intensity_kt >= 50:
        zones.append({"radius_nm": 50, "label": "Storm Force (≥50kt)", "severity": "moderate", "color": "#f97316"})
        zones.append({"radius_nm": 120, "label": "Gale Force (34-49kt)", "severity": "low", "color": "#22c55e"})
    elif intensity_kt >= 34:
        zones.append({"radius_nm": 80, "label": "Gale Force (≥34kt)", "severity": "low", "color": "#22c55e"})
    else:
        # Tropical depression or unknown — show general area
        zones.append({"radius_nm": 60, "label": "Tropical Depression Zone", "severity": "low", "color": "#22c55e"})

    for zone in zones:
        ring = create_circle_polygon(center_lat, center_lon, zone["radius_nm"] * 1.852)  # NM to KM
        features.append({
            "type": "Feature",
            "properties": {
                "label": zone["label"],
                "severity": zone["severity"],
                "fill_color": zone["color"],
                "fill_opacity": 0.2,
                "stroke_color": zone["color"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [ring],
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
