
import httpx
from typing import Optional, Tuple
from utils import fetch_json

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"

async def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[dict]:
    """
    Get driving route from OSRM.
    Returns dict with 'distance_km' and 'duration_min' or None on failure.
    """
    url = f"{OSRM_BASE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}"
    
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, url, {"overview": "false"})
        
        if data and data.get("routes"):
            route = data["routes"][0]
            distance_meters = route.get("distance", 0)
            duration_seconds = route.get("duration", 0)
            
            return {
                "distance_km": round(distance_meters / 1000, 2),
                "duration_min": round(duration_seconds / 60, 0),
                "steps": [] # We could extract steps if needed
            }
            
    return None

async def format_resource_distance(lat, lon, resource_lat, resource_lon):
    """
    Returns string like '3.4km (Driving)' or fallback '3.4km (Line)'
    """
    from utils import haversine # Avoid circular if at top
    
    # Try OSRM
    route = await get_route(resource_lat, resource_lon, lat, lon)
    
    if route:
        return f"{route['distance_km']} km ({int(route['duration_min'])} min drive)"
    else:
        # Fallback
        dist = haversine(lat, lon, resource_lat, resource_lon)
        return f"{round(dist, 1)} km (Linear)"
