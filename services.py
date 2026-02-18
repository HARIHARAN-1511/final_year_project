
import asyncio
import time
import re
import random
import math
import httpx
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from database import SessionLocal
from models import DisasterCache

from config import (
    HTTP_TIMEOUT,
    CACHE_TTL,
    POPULATION_DENSITY,
    RESOURCE_TYPES,

)
import json
from utils import (
    haversine,
    generate_wind_radii_geojson,
    simplify_geojson,
    fetch_json,
    fetch_text,
)
from scoring_engine import (
    calculate_priority_score,
    get_priority_label,
    calculate_news_urgency
)
from routing_service import format_resource_distance, get_route

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def estimate_population_exposure(
    lat: float, lon: float, radius_km: float, country_code: str = ""
) -> dict:
    """
    Estimate population inside a circular impact zone.
    Uses national-level density from WorldPop as an academic approximation.
    """
    cc = country_code.upper()[:2] if country_code else ""
    density = POPULATION_DENSITY.get(cc, POPULATION_DENSITY["default"])
    
    area_km2 = math.pi * radius_km ** 2
    estimated = int(density * area_km2)

    if density > 1000:
        confidence = "High (Urban)"
    elif density < 50:
        confidence = "Low (Rural)"
    else:
        confidence = "Medium"

    return {
        "estimated_population": estimated,
        "area_km2": round(area_km2, 1),
        "density_per_km2": density,
        "data_source": "WorldPop (2020) + PDRDSS Logic",
        "confidence": confidence,
        "method": "Census-based density model",
        "disclaimer": (
            "Population exposure is estimated using public census-based density models. "
            "No mobile tracking is used."
        ),
    }

def get_simulated_resources(severity: str, population_count: int = 0) -> dict:
    """
    Calculate resources based on REAL formulas (WHO/Sphere Standards).
    """
    if severity == "NONE":
        return {"items": [], "disclaimer": "No resources needed."}

    pop = max(1000, population_count)
    items = []
    
    # Water: 15L per person per day
    items.append({
        "name": "Water Purification (Liters/Day)",
        "icon": "💧", 
        "quantity": pop * 15,
        "unit": "liters"
    })
    
    # Shelter: 1 kit per family (5 people)
    items.append({
        "name": "Emergency Shelter Kits",
        "icon": "⛺",
        "quantity": math.ceil(pop / 5),
        "unit": "kits"
    })
    
    # Food: 0.5kg per person
    items.append({
        "name": "Food Rations (Daily)",
        "icon": "🍱",
        "quantity": int(pop * 0.5),
        "unit": "kg"
    })
    
    # Medical: 1 kit per 10k
    items.append({
        "name": "Medical Kits (IEHK)",
        "icon": "🩺",
        "quantity": max(1, int(pop / 10000)),
        "unit": "kits"
    })
    
    return {
        "items": items,
        "disclaimer": "Allocations based on WHO & Sphere Project standards for humanitarian response.",
    }

def get_recommended_teams(disaster_type: str, severity: str) -> list:
    """Deterministic team recommendations based on disaster type + severity."""
    teams = []

    if disaster_type == "earthquake":
        if severity in ("CATASTROPHIC", "SEVERE"):
            teams = [
                {"name": "Urban Search & Rescue (USAR)", "priority": "CRITICAL", "reason": "Building collapse likely — heavy rescue capability needed"},
                {"name": "Emergency Medical Teams (EMT)", "priority": "CRITICAL", "reason": "Mass casualty potential — triage and stabilization"},
                {"name": "Structural Assessment Engineers", "priority": "HIGH", "reason": "Building safety evaluation before re-entry"},
                {"name": "Logistics & Heavy Equipment", "priority": "HIGH", "reason": "Debris clearance and access route restoration"},
                {"name": "K-9 Search Units", "priority": "HIGH", "reason": "Locate trapped individuals under rubble"},
                {"name": "Utilities & Hazmat Teams", "priority": "MEDIUM", "reason": "Gas leak detection and utility shutoff"},
            ]
        elif severity == "MODERATE":
            teams = [
                {"name": "Structural Assessment Engineers", "priority": "HIGH", "reason": "Inspect buildings for damage"},
                {"name": "Emergency Medical Teams (EMT)", "priority": "MEDIUM", "reason": "Treat injuries from falling objects/debris"},
                {"name": "Urban Search & Rescue (USAR)", "priority": "MEDIUM", "reason": "Standby for potential collapse scenarios"},
                {"name": "Utilities Teams", "priority": "MEDIUM", "reason": "Check infrastructure integrity"},
            ]
        else:
            teams = [
                {"name": "Monitoring & Assessment Team", "priority": "LOW", "reason": "Standard seismic monitoring — no immediate action required"},
            ]

    elif disaster_type == "cyclone":
        if severity in ("CATASTROPHIC", "SEVERE"):
            teams = [
                {"name": "Swift Water Rescue", "priority": "CRITICAL", "reason": "Flooding and storm surge — water rescue capability needed"},
                {"name": "Emergency Medical Teams (EMT)", "priority": "CRITICAL", "reason": "Wind/debris injuries and evacuee medical needs"},
                {"name": "Evacuation Coordination", "priority": "CRITICAL", "reason": "Coastal and low-lying area evacuation"},
                {"name": "Logistics & Supply Chain", "priority": "HIGH", "reason": "Pre-position supplies, fuel, generators"},
                {"name": "Communications Teams", "priority": "HIGH", "reason": "Establish backup comms — power outages expected"},
                {"name": "Structural Assessment Engineers", "priority": "MEDIUM", "reason": "Post-storm building safety evaluation"},
            ]
        elif severity == "MODERATE":
            teams = [
                {"name": "Emergency Medical Teams (EMT)", "priority": "MEDIUM", "reason": "Standby for weather-related injuries"},
                {"name": "Evacuation Coordination", "priority": "MEDIUM", "reason": "Monitor low-lying areas for flooding"},
                {"name": "Logistics Teams", "priority": "MEDIUM", "reason": "Prepare emergency supplies and shelter"},
            ]
        else:
            teams = [
                {"name": "Weather Monitoring Team", "priority": "LOW", "reason": "Track storm development — no immediate action required"},
            ]

    return teams

# ---------------------------------------------------------------------------
# API Logic / Helpers
# ---------------------------------------------------------------------------

async def geocode_location(location: str):
    # Check if already coordinates
    parts = [p.strip() for p in location.split(",")]
    if len(parts) == 2:
        try:
            lat, lon = float(parts[0]), float(parts[1])
            return {
                "lat": lat, "lon": lon,
                "display_name": f"{lat:.4f}, {lon:.4f}",
                "confidence": "HIGH",
                "importance": 1.0,
                "source": "direct_coordinates",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except ValueError:
            pass

    async with httpx.AsyncClient() as client:
        # Try 1: Exact
        data = await fetch_json(client, "https://nominatim.openstreetmap.org/search", {
            "q": location, "format": "json", "limit": 5, "addressdetails": 1
        })
        # Try 2: Cleaned — strip USGS-style prefixes to get the city/region name
        if not data:
            clean_loc = location
            # Handle: "18 km W of Punitaqui", "23 km NNW of X", "18 km from X", "100km SSE of X"
            clean_loc = re.sub(r'^\d+\s*km\s*(?:[NSEW]{1,3}\s+)?(?:of|from)\s+', '', clean_loc, flags=re.IGNORECASE)
            # Handle: "near X", "south of X", "off the coast of X"
            clean_loc = re.sub(r'^(?:near|south|north|east|west|off\s+the\s+coast)\s+(?:of\s+)?', '', clean_loc, flags=re.IGNORECASE)
            if clean_loc != location and clean_loc.strip():
                data = await fetch_json(client, "https://nominatim.openstreetmap.org/search", {
                    "q": clean_loc, "format": "json", "limit": 5, "addressdetails": 1
                })

    if not data:
        return None

    top = data[0]
    importance = float(top.get("importance", 0))
    confidence = "HIGH" if importance > 0.6 else ("MEDIUM" if importance > 0.3 else "LOW")

    alternatives = []
    for alt in data[1:4]:
        alternatives.append({
            "display_name": alt.get("display_name", ""),
            "lat": float(alt["lat"]),
            "lon": float(alt["lon"]),
        })

    return {
        "lat": float(top["lat"]),
        "lon": float(top["lon"]),
        "display_name": top.get("display_name", location),
        "confidence": confidence,
        "importance": importance,
        "alternatives": alternatives,
        "source": "nominatim",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

async def fetch_earthquakes(lat: float, lon: float, radius_km: float, days: int, min_mag: float):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, "https://earthquake.usgs.gov/fdsnws/event/1/query", {
            "format": "geojson", "latitude": lat, "longitude": lon,
            "maxradiuskm": radius_km, "starttime": start.isoformat(),
            "endtime": end.isoformat(), "minmagnitude": min_mag,
            "orderby": "magnitude", "limit": 50,
        })
    
    ts = datetime.now(timezone.utc).isoformat()
    
    # DB Fallback
    if not data:
        async with SessionLocal() as db:
            result = await db.execute(select(DisasterCache).where(DisasterCache.type == "earthquake"))
            cached_rows = result.scalars().all()
            features = []
            for row in cached_rows:
                d = haversine(lat, lon, row.lat, row.lon)
                if d <= radius_km:
                    features.append(row.data_json)
            if features:
                data = {"features": features}

    if not data or not data.get("features"):
        return {
            "events": [], "count": 0, "message": f"No significant events within {int(radius_km)}km.",
            "source": "USGS (Offline)", "timestamp": ts, "shakemap": None,
            "nearby_cities": [], "pager_data": None, "tectonic_summary": None,
        }

    events = []
    shakemap_geojson = None
    nearby_cities = []
    pager_data = None
    tectonic_summary = None
    
    for f in data["features"]:
        props = f["properties"]
        coords = f["geometry"]["coordinates"]
        ev = {
            "id": f.get("id"),
            "magnitude": props.get("mag"),
            "place": props.get("place", ""),
            "time": datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc).isoformat() if props.get("time") else None,
            "depth_km": coords[2] if len(coords) > 2 else None,
            "lat": coords[1], "lon": coords[0],
            "tsunami": props.get("tsunami", 0),
            "felt": props.get("felt"),
            "alert": props.get("alert"),
            "mmi": props.get("mmi"),
            "detail_url": props.get("detail"),
            "significance": props.get("sig", 0),
            "event_type": props.get("type", "earthquake"),
            "status": props.get("status", ""),
            "url": props.get("url", ""),
        }
        events.append(ev)

    # Fetch rich detail for the strongest event from USGS detail API
    if events and events[0].get("detail_url"):
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                detail = await fetch_json(client, events[0]["detail_url"])
                if detail:
                    products = detail.get("properties", {}).get("products", {})
                    
                    # --- ShakeMap ---
                    sm_prods = products.get("shakemap", [])
                    if sm_prods:
                        contents = sm_prods[0].get("contents", {})
                        for key in ["download/cont_mi.json", "download/cont_mmi.json"]:
                            if key in contents:
                                shakemap_geojson = await fetch_json(client, contents[key]["url"])
                                break
                    
                    # --- Nearby Cities ---
                    nc_prods = products.get("nearby-cities", [])
                    if nc_prods:
                        nc_contents = nc_prods[0].get("contents", {})
                        if "nearby-cities.json" in nc_contents:
                            nc_data = await fetch_json(client, nc_contents["nearby-cities.json"]["url"])
                            if nc_data and isinstance(nc_data, list):
                                nearby_cities = nc_data[:10]
                    
                    # --- PAGER (Loss estimates) ---
                    lp_prods = products.get("losspager", [])
                    if lp_prods:
                        lp = lp_prods[0]
                        lp_props = lp.get("properties", {})
                        pager_data = {
                            "alert_level": lp_props.get("alertlevel", ""),
                            "max_mmi": lp_props.get("maxmmi", ""),
                        }
                        # Try to get exposure data
                        lp_contents = lp.get("contents", {})
                        if "json/exposures.json" in lp_contents:
                            try:
                                exp_data = await fetch_json(client, lp_contents["json/exposures.json"]["url"])
                                if exp_data:
                                    pager_data["exposures"] = exp_data
                            except Exception:
                                pass
                    
                    # --- Tectonic Summary ---
                    ts_prods = products.get("general-text", [])
                    if ts_prods:
                        ts_contents = ts_prods[0].get("contents", {})
                        if "" in ts_contents:
                            try:
                                raw_text = await fetch_text(client, ts_contents[""]["url"])
                                if raw_text:
                                    # Strip HTML tags for clean text
                                    import re as _re
                                    clean = _re.sub(r'<[^>]+>', '', raw_text)
                                    tectonic_summary = clean.strip()[:1000]
                            except Exception:
                                pass
                    
            except Exception:
                pass

    return {
        "events": events, "count": len(events), "message": None,
        "source": "USGS", "timestamp": ts, "shakemap": shakemap_geojson,
        "nearby_cities": nearby_cities, "pager_data": pager_data,
        "tectonic_summary": tectonic_summary,
    }

async def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather conditions from Open-Meteo (free, no API key)."""
    ts = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, "https://api.open-meteo.com/v1/forecast", {
            "latitude": lat, "longitude": lon,
            "current_weather": "true",
            "hourly": "visibility,relative_humidity_2m",
            "forecast_days": 1,
        })
    if not data or not data.get("current_weather"):
        return {"available": False, "source": "Open-Meteo", "timestamp": ts}
    
    cw = data["current_weather"]
    # Map WMO weather codes to descriptions
    WMO_CODES = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    
    # Get current hour's visibility and humidity
    visibility = None
    humidity = None
    hourly = data.get("hourly", {})
    if hourly.get("visibility"):
        visibility = hourly["visibility"][0]  # first hour
    if hourly.get("relative_humidity_2m"):
        humidity = hourly["relative_humidity_2m"][0]
    
    return {
        "available": True,
        "temperature_c": cw.get("temperature"),
        "windspeed_kmh": cw.get("windspeed"),
        "wind_direction": cw.get("winddirection"),
        "weather_code": cw.get("weathercode"),
        "weather_desc": WMO_CODES.get(cw.get("weathercode", -1), "Unknown"),
        "is_day": cw.get("is_day", 1),
        "visibility_m": visibility,
        "humidity_pct": humidity,
        "source": "Open-Meteo",
        "timestamp": ts,
    }

async def fetch_cyclones(lat: float, lon: float):
    ts = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, "https://www.nhc.noaa.gov/CurrentSummaries.json")
        if not data:
             data = await fetch_json(client, "https://www.nhc.noaa.gov/gis/forecast/archive/active_storms.json")

    # DB Fallback
    if not data:
        async with SessionLocal() as db:
            result = await db.execute(select(DisasterCache).where(DisasterCache.type == "cyclone"))
            cached_rows = result.scalars().all()
            if cached_rows:
                active_storms = [row.data_json for row in cached_rows]
                data = {"activeStorms": active_storms}

    if not data or not data.get("activeStorms"):
        return {"storms": [], "count": 0, "message": "No active cyclones.", "source": "NOAA NHC (Offline)", "timestamp": ts, "wind_radii": None}

    storms = []
    for storm in data["activeStorms"]:
        storm_info = {
            "id": storm.get("binNumber", ""),
            "name": storm.get("name", "Unknown"),
            "classification": storm.get("classification", ""),
            "intensity": storm.get("intensity", ""),
            "pressure": storm.get("pressure", ""),
            "lat": storm.get("lat"),
            "lon": storm.get("lon"),
            "movement_dir": storm.get("movementDir", ""),
            "movement_speed": storm.get("movementSpeed", ""),
            "last_update": storm.get("lastUpdate", ""),
            "advisory_url": storm.get("url", ""),
        }

        # Parse lat/lon from string if needed
        if isinstance(storm_info["lat"], str):
            try:
                lat_val = float(storm_info["lat"].replace("N", "").replace("S", "-").strip())
                lon_val = float(storm_info["lon"].replace("W", "").replace("E", "").strip())
                if "W" in str(storm.get("lon", "")):
                    lon_val = -lon_val
                if "S" in str(storm.get("lat", "")):
                    lat_val = -lat_val
                storm_info["lat"] = lat_val
                storm_info["lon"] = lon_val
            except (ValueError, TypeError):
                storm_info["lat"] = None
                storm_info["lon"] = None

        storms.append(storm_info)

    # Generate wind radii polygons for closest storm
    wind_radii = None
    if storms:
        closest = min(storms, key=lambda s: haversine(lat, lon, s.get("lat") or 0, s.get("lon") or 0))
        if closest.get("lat") and closest.get("lon"):
            wind_radii = generate_wind_radii_geojson(closest)

    return {"storms": storms, "count": len(storms), "source": "NOAA NHC", "timestamp": ts, "wind_radii": wind_radii}

async def fetch_news(query: str, timespan: str = "24h"):
    ts = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, "https://api.gdeltproject.org/api/v2/doc/doc", {
            "query": query, "mode": "ArtList", "format": "json", "maxrecords": 20, "timespan": timespan, "sort": "DateDesc"
        })

    if not data or not data.get("articles"):
         return {"articles": [], "count": 0, "message": "No news.", "source": "GDELT", "timestamp": ts}

    articles = []
    for art in data["articles"][:15]:
        articles.append({
            "title": art.get("title", ""),
            "url": art.get("url", ""),
            "source": art.get("domain", art.get("source", "")),
            "date": art.get("seendate", ""),
            "image": art.get("socialimage", ""),
        })

    return {"articles": articles, "count": len(articles), "source": "GDELT", "timestamp": ts}

async def fetch_resources(lat: float, lon: float, radius_m: int = 15000):
    ts = datetime.now(timezone.utc).isoformat()
    query = f"""[out:json][timeout:10];(node["amenity"="hospital"](around:{radius_m},{lat},{lon});way["amenity"="hospital"](around:{radius_m},{lat},{lon});node["amenity"="fire_station"](around:{radius_m},{lat},{lon});way["amenity"="fire_station"](around:{radius_m},{lat},{lon});node["amenity"="police"](around:{radius_m},{lat},{lon});way["amenity"="police"](around:{radius_m},{lat},{lon}););out center 50;"""
    
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, "https://overpass-api.de/api/interpreter", {"data": query})

    if not data or not data.get("elements"):
        return {"resources": [], "all": [], "count": 0, "message": "No resources found.", "source": "OpenStreetMap", "timestamp": ts}

    resources = {"hospitals": [], "fire_stations": [], "police": []}
    all_res = []
    for el in data["elements"]:
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        name = tags.get("name", tags.get("name:en", "Unnamed"))

        r_lat = el.get("lat") or el.get("center", {}).get("lat")
        r_lon = el.get("lon") or el.get("center", {}).get("lon")

        if not r_lat or not r_lon:
            continue

        entry = {
            "name": name,
            "lat": r_lat,
            "lon": r_lon,
            "address": tags.get("addr:full", tags.get("addr:street", "")),
            "phone": tags.get("phone", tags.get("contact:phone", "")),
            "type": amenity
        }

        if amenity == "hospital":
            entry["emergency"] = tags.get("emergency", "")
            resources["hospitals"].append(entry)
        elif amenity == "fire_station":
            resources["fire_stations"].append(entry)
        elif amenity == "police":
            resources["police"].append(entry)
        
        all_res.append(entry)

    return {"resources": resources, "all": all_res, "count": len(all_res), "source": "OpenStreetMap", "timestamp": ts}

async def get_live_feed_data():
    # Helper for parsing lat/lon from NHC format (e.g. "15.2N")
    def parse_coord(val):
        if not isinstance(val, str): return val
        try:
            v = float(val.replace("N", "").replace("S", "").replace("E", "").replace("W", "").strip())
            if "S" in val or "W" in val: v = -v
            return v
        except: return None

    ts_now = datetime.now(timezone.utc).isoformat()
    events = []
    
    async with httpx.AsyncClient() as client:
        # 1. Earthquakes
        try:
            eq = await fetch_json(client, "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson")
            if eq and eq.get("features"):
                for f in eq["features"][:50]:
                    props = f["properties"]
                    events.append({
                        "type": "earthquake", 
                        "title": f"M{props.get('mag')} Earthquake",
                        "location": props.get("place", "Unknown Location"), 
                        "lat": f["geometry"]["coordinates"][1], 
                        "lon": f["geometry"]["coordinates"][0],
                        "time": datetime.fromtimestamp(props["time"]/1000, tz=timezone.utc).isoformat(),
                        "magnitude": props.get("mag"),
                        "depth_km": f["geometry"]["coordinates"][2],
                        "tsunami": props.get("tsunami"),
                        "felt": props.get("felt"),
                        "source": "USGS"
                    })
        except Exception:
            pass

        # 2. Cyclones
        try:
            cy = await fetch_json(client, "https://www.nhc.noaa.gov/CurrentSummaries.json")
            if not cy:
                 cy = await fetch_json(client, "https://www.nhc.noaa.gov/gis/forecast/archive/active_storms.json")
            
            if cy and cy.get("activeStorms"):
                for storm in cy["activeStorms"]:
                    lat_val = parse_coord(storm.get('lat'))
                    lon_val = parse_coord(storm.get('lon'))
                    events.append({
                        "type": "cyclone",
                        "title": f"Cyclone {storm.get('name', 'Unknown')}",
                        "location": f"Lat: {storm.get('lat')}, Lon: {storm.get('lon')}",
                        "lat": lat_val,
                        "lon": lon_val,
                        "intensity": storm.get('intensity', '0'),
                        "time": datetime.now(timezone.utc).isoformat(), # Real-time feed
                        "source": "NOAA NHC"
                    })
        except Exception:
            pass

    # Sort by time desc
    events.sort(key=lambda x: x.get("time") or "", reverse=True)
    
    eq_count = sum(1 for e in events if e["type"] == "earthquake")
    cy_count = sum(1 for e in events if e["type"] == "cyclone")
    total = len(events)
    
    # Limit to 5 events for the landing page feed
    events = events[:5]
    
    return {"events": events, "timestamp": ts_now, "earthquake_count": eq_count, "cyclone_count": cy_count, "total": total}

# ---------------------------------------------------------------------------
# AI Analysis (OpenRouter - OpenAI Compatible)
# ---------------------------------------------------------------------------

async def get_ai_analysis(analysis_data: dict, disaster_type: str, location_name: str) -> dict:
    """AI Analysis disabled."""
    return {"available": False, "summary": "AI analysis disabled", "model": None}

# ---------------------------------------------------------------------------
# MAIN AGGREGATOR
# ---------------------------------------------------------------------------

async def analyze_disaster_impact(lat: float, lon: float, disaster_type: str, location_name: str):
    """
    Aggregate data + Scoring + Routing.
    Returns data structured EXACTLY as app.js expects for rendering.
    """
    ts_start = time.time()
    
    # 1. Fetch Data in parallel
    task_disaster = None
    if disaster_type == "earthquake":
        task_disaster = fetch_earthquakes(lat, lon, 500, 30, 2.5)
    else:
        task_disaster = fetch_cyclones(lat, lon)
        
    # Build a better GDELT query — if location is just coordinates, reverse-geocode it
    news_query = f"{disaster_type} {location_name}"
    # If location_name looks like raw coordinates, try to get a better name
    coord_pattern = re.match(r'^-?\d+\.\d+,\s*-?\d+\.\d+$', location_name.strip())
    if coord_pattern:
        # Use reverse geocoding to get a human-readable name for GDELT search
        try:
            async with httpx.AsyncClient() as client:
                rev_data = await fetch_json(client, "https://nominatim.openstreetmap.org/reverse", {
                    "lat": lat, "lon": lon, "format": "json", "zoom": 6
                })
                if rev_data and rev_data.get("display_name"):
                    # Extract just the country/region part
                    parts = rev_data["display_name"].split(",")
                    region_name = ", ".join(p.strip() for p in parts[:3])
                    news_query = f"{disaster_type} {region_name}"
        except Exception:
            pass

    task_news = fetch_news(news_query)
    task_resources = fetch_resources(lat, lon)
    task_weather = fetch_weather(lat, lon)
    
    disaster_data, news_data, resources_data, weather_data = await asyncio.gather(
        task_disaster, task_news, task_resources, task_weather, return_exceptions=True
    )
    
    # Normalize results (handle exceptions)
    if isinstance(disaster_data, Exception): disaster_data = None
    if isinstance(news_data, Exception): news_data = None
    if isinstance(resources_data, Exception): resources_data = None
    if isinstance(weather_data, Exception): weather_data = None
    
    # =========================================================================
    # 2. Build disaster_info (what app.js renderDisasterInfo expects)
    # =========================================================================
    severity = "NONE"
    disaster_info = {}
    shakemap = None
    storms_wind_radii = None
    concerns = []
    
    if disaster_type == "earthquake" and disaster_data and disaster_data.get("count", 0) > 0:
        events = disaster_data["events"]
        # Find strongest event
        strongest = max(events, key=lambda e: e.get("magnitude") or 0)
        max_mag = strongest.get("magnitude") or 0
        
        if max_mag >= 7.0: severity = "CATASTROPHIC"
        elif max_mag >= 6.0: severity = "SEVERE"
        elif max_mag >= 4.5: severity = "MODERATE"
        else: severity = "MINOR"
        
        disaster_info = {
            "what": f"M{max_mag} Earthquake",
            "where": strongest.get("place", location_name),
            "when": strongest.get("time"),
            "magnitude": max_mag,
            "depth_km": strongest.get("depth_km"),
            "total_events": disaster_data["count"],
            "mmi": strongest.get("mmi"),
            "alert_level": strongest.get("alert"),
            "tsunami": strongest.get("tsunami", 0),
            "felt": strongest.get("felt"),
            "distance_km": round(haversine(lat, lon, strongest["lat"], strongest["lon"]), 1),
            "time_ago": (datetime.now(timezone.utc) - datetime.fromisoformat(strongest["time"].replace("Z", "+00:00"))).total_seconds(),
            "significance": strongest.get("significance", 0),
            "status": strongest.get("status", ""),
            "event_url": strongest.get("url", ""),
            "event_id": strongest.get("id", ""),
        }
        
        # MMI intensity description
        mmi_val = strongest.get("mmi") or 0
        MMI_DESCRIPTIONS = {
            1: "Not Felt", 2: "Weak", 3: "Weak", 4: "Light",
            5: "Moderate", 6: "Strong", 7: "Very Strong",
            8: "Severe", 9: "Violent", 10: "Extreme"
        }
        disaster_info["mmi_description"] = MMI_DESCRIPTIONS.get(int(round(mmi_val)), "Unknown")
        
        # Depth classification
        depth = strongest.get("depth_km") or 0
        if depth < 20: disaster_info["depth_class"] = "Shallow (< 20 km)"
        elif depth < 70: disaster_info["depth_class"] = "Intermediate (20-70 km)"
        elif depth < 300: disaster_info["depth_class"] = "Deep (70-300 km)"
        else: disaster_info["depth_class"] = "Very Deep (> 300 km)"
        
        # ShakeMap from fetched data
        shakemap = disaster_data.get("shakemap")
        
        # Generate concerns
        if max_mag >= 6.0:
            concerns.append("High risk of building collapse in unreinforced structures")
            concerns.append("Expect significant aftershock sequence — monitor for 72+ hours")
        if max_mag >= 5.0:
            concerns.append("Possible road and infrastructure damage — access routes may be blocked")
        if strongest.get("tsunami"):
            concerns.append("⚠ TSUNAMI WARNING — Coastal evacuation may be required")
        if strongest.get("depth_km") and strongest["depth_km"] < 20:
            concerns.append("Shallow earthquake — surface damage likely more severe")
        if max_mag >= 4.0:
            concerns.append("Utilities (gas, water, power) may be disrupted — check for gas leaks")
        if max_mag >= 5.5:
            concerns.append("Liquefaction risk in areas with saturated sandy soils")
            concerns.append("Landslide risk in hilly and mountainous terrain")
        if disaster_data.get("count", 0) > 5:
            concerns.append(f"Elevated seismic activity — {disaster_data['count']} events detected in the region")
        
    elif disaster_type == "cyclone" and disaster_data and disaster_data.get("count", 0) > 0:
        storms = disaster_data["storms"]
        # Find closest storm
        closest = min(storms, key=lambda s: haversine(lat, lon, s.get("lat") or 0, s.get("lon") or 0))
        
        intensity = closest.get("intensity", "")
        try:
            int_val = int(intensity)
        except (ValueError, TypeError):
            int_val = 0
            
        if int_val >= 115: severity = "CATASTROPHIC"
        elif int_val >= 65: severity = "SEVERE"
        elif int_val >= 34: severity = "MODERATE"
        else: severity = "MINOR" if int_val > 0 else "NONE"
        
        disaster_info = {
            "what": f"Cyclone {closest.get('name', 'Unknown')}",
            "where": f"{closest.get('movement_dir', '')} — {closest.get('classification', '')}",
            "intensity_kt": intensity,
            "classification": closest.get("classification", ""),
            "total_active": disaster_data["count"],
            "pressure": closest.get("pressure"),
        }
        
        storms_wind_radii = disaster_data.get("wind_radii")
        
        # Generate concerns
        if int_val >= 65:
            concerns.append("Severe wind damage expected — secure structures and evacuate if needed")
            concerns.append("Storm surge flooding likely in coastal and low-lying areas")
        concerns.append("Power outages expected — deploy backup communications")
        if int_val >= 34:
            concerns.append("Flooding risk from heavy rainfall — monitor river and drainage levels")
    else:
        disaster_info = {"message": f"No significant {disaster_type} events detected near this location."}

    # =========================================================================
    # 3. Population Exposure
    # =========================================================================
    impact_radius = 50 if severity in ("SEVERE", "CATASTROPHIC") else (30 if severity == "MODERATE" else 10)
    pop_data = estimate_population_exposure(lat, lon, impact_radius)
    
    # Multi-zone population breakdown
    pop_zones = []
    if severity != "NONE":
        zone_radii = [
            ("Severe Impact", impact_radius * 0.3, "#dc2626"),
            ("Moderate Impact", impact_radius * 0.6, "#f97316"),
            ("Minor Impact", impact_radius, "#eab308"),
        ]
        for zone_name, zone_r, zone_color in zone_radii:
            zp = estimate_population_exposure(lat, lon, zone_r)
            pop_zones.append({
                "name": zone_name,
                "radius_km": round(zone_r, 1),
                "population": zp["estimated_population"],
                "color": zone_color,
            })
    
    # =========================================================================
    # 4. News
    # =========================================================================
    news_urgency_score = 0
    news_result = {"articles": [], "count": 0, "message": "No news found.", "source": "GDELT", "timestamp": datetime.now(timezone.utc).isoformat()}
    if news_data and news_data.get("articles"):
        news_result = news_data
        news_urgency_score = calculate_news_urgency(news_data["articles"])
        
    # =========================================================================
    # 5. Resources (structured as app.js expects: resources.data.hospitals etc.)
    # =========================================================================
    resources_result = {
        "data": {"hospitals": [], "fire_stations": [], "police": []},
        "count": 0,
        "source": "OpenStreetMap",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    min_dist_km = 999
    nearest_resource = None
    
    if resources_data and resources_data.get("resources"):
        resources_result = {
            "data": resources_data["resources"],
            "count": resources_data["count"],
            "source": resources_data["source"],
            "timestamp": resources_data["timestamp"]
        }
        # Find closest resource
        for r in resources_data.get("all", []):
            d = haversine(lat, lon, r["lat"], r["lon"])
            if d < min_dist_km:
                min_dist_km = d
                nearest_resource = r
    
    if not resources_result["count"]:
        resources_result["message"] = "No emergency facilities found within search radius."
    
    # =========================================================================
    # 6. Scoring
    # =========================================================================
    priority_score = calculate_priority_score(
        severity, 
        pop_data["estimated_population"],
        min_dist_km if min_dist_km < 999 else -1,
        news_urgency_score
    )
    priority_label = get_priority_label(priority_score)
    
    # =========================================================================
    # 7. Real Routing (if critical/high)
    # =========================================================================
    if priority_score > 40 and nearest_resource:
        route_info = await get_route(nearest_resource["lat"], nearest_resource["lon"], lat, lon)
        if route_info:
            nearest_resource["driving_dist"] = f"{route_info['distance_km']} km"
            nearest_resource["driving_time"] = f"{route_info['duration_min']} min"
            
    # =========================================================================
    # 8. Teams + Allocated Resources
    # =========================================================================
    teams = get_recommended_teams(disaster_type, severity)
    allocated_resources = get_simulated_resources(severity, pop_data["estimated_population"])
    
    # =========================================================================
    # 9. Data Sources (for freshness badges)
    # =========================================================================
    ts_now = datetime.now(timezone.utc).isoformat()
    data_sources = {
        "disaster": {
            "source": "USGS" if disaster_type == "earthquake" else "NOAA NHC",
            "status": "ok" if disaster_data else "error",
            "timestamp": disaster_data.get("timestamp", ts_now) if disaster_data else ts_now
        },
        "news": {
            "source": "GDELT",
            "status": "ok" if (news_data and news_data.get("articles")) else "error",
            "timestamp": news_data.get("timestamp", ts_now) if news_data else ts_now
        },
        "resources": {
            "source": "OpenStreetMap",
            "status": "ok" if (resources_data and resources_data.get("count", 0) > 0) else "error",
            "timestamp": resources_data.get("timestamp", ts_now) if resources_data else ts_now
        },
        "imagery": {
            "source": "Esri/Maxar",
            "status": "pre-disaster",
            "timestamp": ts_now
        }
    }
    
    elapsed = round(time.time() - ts_start, 2)
    
    # =========================================================================
    # RETURN — structured exactly as app.js expects
    # =========================================================================
    result = {
        # Top bar
        "priority": priority_label,
        "priority_score": priority_score,
        "severity": severity,
        "disaster_type": disaster_type,
        "location": location_name,
        "coordinates": {"lat": lat, "lon": lon},
        "timestamp": ts_now,
        "elapsed_seconds": elapsed,
        
        # Panels
        "disaster_info": disaster_info,
        "population_exposure": pop_data,
        "population_zones": pop_zones,
        "teams": teams,
        "concerns": concerns,
        "resources": resources_result,
        "allocated_resources": allocated_resources,
        "nearest_resource": nearest_resource,
        
        # News
        "news": news_result,
        
        # Map overlays
        "shakemap": shakemap,
        "storms_wind_radii": storms_wind_radii,
        
        # Enriched data
        "nearby_cities": disaster_data.get("nearby_cities", []) if disaster_data else [],
        "pager_data": disaster_data.get("pager_data") if disaster_data else None,
        "tectonic_summary": disaster_data.get("tectonic_summary") if disaster_data else None,
        "recent_events": disaster_data.get("events", [])[:20] if disaster_data else [],
        "weather": weather_data if weather_data else {"available": False},
        
        # Freshness
        "data_sources": data_sources,
    }
    
    # AI analysis disabled as per user request
    result["ai_analysis"] = {"available": False, "summary": "AI analysis disabled", "model": None}
    
    return result

