
# Post-Disaster Rescue Decision Support System (PDRDSS)
# Configuration and Constants

HTTP_TIMEOUT = 20.0  # seconds per external API call (USGS query can take 15s+)
CACHE_TTL = 300      # seconds for server-side cache

# ---------------------------------------------------------------------------
# WorldPop population density lookup  (persons per km²)
# Source: WorldPop 2020 national estimates — academic approximation
# ---------------------------------------------------------------------------
POPULATION_DENSITY = {
    "default": 50,
    "JP": 347, "IN": 464, "BD": 1265, "PH": 368, "ID": 151,
    "CN": 153, "PK": 287, "NG": 226, "US": 36, "MX": 66,
    "TR": 110, "IR": 52, "IT": 206, "NP": 203, "MM": 83,
    "HT": 414, "GT": 167, "CL": 26, "PE": 26, "EC": 71,
    "CO": 46, "VE": 37, "BR": 25, "AF": 60, "ET": 115,
    "KE": 94, "TZ": 67, "MZ": 40, "MG": 47, "VN": 314,
    "TH": 137, "LK": 341, "TW": 673, "KR": 527, "DE": 240,
    "GB": 281, "FR": 119, "ES": 94, "GR": 83, "PT": 112,
}

# ---------------------------------------------------------------------------
# Simulated Resource Allocation  (academic demonstration)
# ---------------------------------------------------------------------------
RESOURCE_TYPES = [
    {"name": "Water Purification Units", "icon": "💧", "unit": "units"},
    {"name": "Emergency Shelter Kits", "icon": "⛺", "unit": "kits"},
    {"name": "Medical Supply Crates", "icon": "🩺", "unit": "crates"},
    {"name": "SAR Equipment Sets", "icon": "🔦", "unit": "sets"},
    {"name": "Communication Radios", "icon": "📻", "unit": "units"},
    {"name": "Portable Generators", "icon": "⚡", "unit": "units"},
    {"name": "Food Ration Packages", "icon": "🍱", "unit": "packages"},
    {"name": "Thermal Blankets", "icon": "🛏️", "unit": "bundles"},
    {"name": "First Aid Stations", "icon": "🏥", "unit": "stations"},
    {"name": "Evacuation Vehicles", "icon": "🚐", "unit": "vehicles"},
]

# ---------------------------------------------------------------------------
# Security Config
# ---------------------------------------------------------------------------
SECRET_KEY = "your-secret-key-keep-it-secret"  # CHANGE THIS IN PRODUCTION!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ---------------------------------------------------------------------------
# AI / LLM Config — Grok (xAI)
# ---------------------------------------------------------------------------
import os
GROK_API_KEY = os.environ.get("GROK_API_KEY", "")   # set via .env or system env var
GROK_MODEL = "grok-3-mini"  # Free-tier xAI model
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
