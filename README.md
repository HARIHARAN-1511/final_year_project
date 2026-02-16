# 🌍 PDRDSS — Post-Disaster Rescue Decision Support System

> **Real-time disaster intelligence platform** that aggregates live earthquake, cyclone, news, and resource data to assist emergency responders with data-driven rescue prioritization.

⚠️ **Academic Prototype** — This is a final-year project and is *not* a certified emergency management tool.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Data Sources & APIs](#-data-sources--apis)
- [Scoring Engine](#-scoring-engine)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Docker Deployment](#-docker-deployment)
- [Screenshots](#-screenshots)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Live Disaster Feed** | Real-time earthquake (USGS) and cyclone (NOAA NHC) data displayed on an interactive map |
| **Geocoding & Search** | Search any location by name or coordinates with confidence scoring |
| **Impact Analysis** | Aggregated analysis combining seismic data, population exposure, nearby resources, and news |
| **Priority Scoring** | Weighted multi-factor scoring engine (severity, population, resource distance, news urgency) |
| **Resource Mapping** | Nearby hospitals, fire stations, and police stations via OpenStreetMap Overpass API |
| **Population Estimation** | Circular impact zone population exposure using WorldPop national density data |
| **News Integration** | Real-time disaster news from GDELT DOC 2.0 API with urgency keyword analysis |
| **Damage Zones** | GeoJSON-based damage zone visualization (epicentral, moderate, light) on Leaflet maps |
| **Rescue Team Recommendations** | Deterministic team allocation based on disaster type and severity |
| **Resource Allocation** | WHO/Sphere Standards-based resource calculation (water, shelter, medical, SAR equipment) |
| **Wind Field Visualization** | Cyclone wind radii polygons (34kt, 50kt, 64kt force zones) rendered on map |
| **User Authentication** | JWT-based login with role-based access (admin/user) |
| **Analysis History** | Logged past analyses with filtering, sorting, and analytics dashboard |
| **Dark Emergency Theme** | Professional dark UI optimized for emergency operations center readability |
| **Docker Support** | Containerized deployment with Docker and Docker Compose |

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.9+** | Core language |
| **FastAPI** | Async web framework & REST API |
| **Uvicorn** | ASGI server |
| **SQLAlchemy (Async)** | ORM with async session support |
| **aiosqlite** | Async SQLite driver |
| **httpx** | Async HTTP client for external API calls |
| **passlib + bcrypt** | Password hashing |
| **python-jose** | JWT token generation & validation |

### Frontend
| Technology | Purpose |
|---|---|
| **HTML5 / CSS3 / JavaScript** | Core web technologies |
| **Leaflet.js** | Interactive map rendering |
| **Chart.js** | Analytics data visualization |
| **Custom CSS** | Dark emergency operations theme |

### External APIs
| API | Data Provided |
|---|---|
| **USGS Earthquake API** | Real-time seismic event data |
| **NOAA NHC (GIS)** | Active cyclone/hurricane advisories |
| **GDELT DOC 2.0** | Real-time disaster news articles |
| **OpenStreetMap Overpass** | Nearby emergency resources (hospitals, fire stations, police) |
| **Nominatim (OSM)** | Geocoding — place name to coordinates |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Browser)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Landing  │ │Dashboard │ │ History  │ │Analytics│ │
│  │  Page    │ │  + Map   │ │  Logs    │ │ Charts │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
│       └─────────────┴────────────┴───────────┘      │
└──────────────────────┬──────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐            │
│  │  Routes  │ │ Services │ │  Scoring  │            │
│  │ (API)    │→│ (Logic)  │→│  Engine   │            │
│  └──────────┘ └────┬─────┘ └───────────┘            │
│  ┌──────────┐      │       ┌───────────┐            │
│  │   Auth   │      │       │   Utils   │            │
│  │  (JWT)   │      │       │ (Cache,   │            │
│  └──────────┘      │       │  Geo)     │            │
│                    │       └───────────┘            │
└────────────────────┼────────────────────────────────┘
                     │ Async HTTP (httpx)
    ┌────────────────┼────────────────────┐
    ▼                ▼                    ▼
┌────────┐    ┌──────────┐       ┌──────────────┐
│  USGS  │    │   NOAA   │       │   GDELT /    │
│Earthquakes│ │ Cyclones │       │ OSM Overpass │
└────────┘    └──────────┘       └──────────────┘
```

---

## 📊 Scoring Engine

The priority scoring engine uses a **weighted multi-factor formula** to produce a 0–100 rescue priority score:

```
Score = (0.4 × Severity) + (0.3 × Population) + (0.2 × Resource Distance) + (0.1 × News Urgency)
```

| Factor | Weight | Scale | Source |
|---|---|---|---|
| **Severity** | 40% | Categorical → 0–100 | Magnitude/intensity mapping |
| **Population Exposure** | 30% | Log₁₀ scale → 0–100 | WorldPop density × impact area |
| **Resource Distance** | 20% | Linear km → 0–100 | Nearest hospital/station via OSM |
| **News Urgency** | 10% | Keyword analysis → 0–100 | GDELT headline keyword scoring |

### Priority Labels

| Score Range | Label |
|---|---|
| 85–100 | 🔴 **CRITICAL** |
| 60–84 | 🟠 **HIGH** |
| 30–59 | 🟡 **MEDIUM** |
| 0–29 | 🟢 **LOW** |

---

## 📁 Project Structure

```
PRDSSS/
├── main.py                 # FastAPI app entry point & frontend routes
├── routes.py               # API route definitions
├── services.py             # Core business logic & external API integration
├── scoring_engine.py       # Multi-factor priority scoring algorithm
├── models.py               # SQLAlchemy ORM models (User, AnalysisLog, Cache)
├── database.py             # Async database engine & session factory
├── auth.py                 # JWT authentication & password hashing
├── config.py               # Configuration constants & resource definitions
├── utils.py                # Caching, HTTP helpers, geospatial utilities
├── routing_service.py      # Distance formatting & routing helpers
├── background_tasks.py     # Background task scheduling
├── create_admin.py         # Admin user creation script
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Container orchestration
├── .gitignore              # Git ignore rules
│
└── static/                 # Frontend assets
    ├── index.html           # Landing page with live disaster feed
    ├── dashboard.html       # Analysis dashboard with interactive map
    ├── login.html           # User authentication page
    ├── history.html         # Past analysis logs viewer
    ├── analytics.html       # Analytics charts & statistics
    ├── css/
    │   ├── landing.css      # Landing page styles
    │   └── style.css        # Dashboard & global styles
    └── js/
        ├── landing.js       # Live feed, search, & landing logic
        ├── app.js           # Dashboard map, analysis, & rendering
        ├── auth.js          # Token management & auth helpers
        ├── history.js       # History page logic
        └── analytics.js     # Chart rendering & stats
```

---

## 🚀 Installation

### Prerequisites
- **Python 3.9+**
- **pip** (Python package manager)
- **Git**

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/HARIHARAN-1511/final_year_project.git
   cd final_year_project
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create an admin user** (optional — for authenticated features)
   ```bash
   python create_admin.py
   ```

5. **Run the application**
   ```bash
   python main.py
   ```
   The server starts at **http://localhost:8000**

---

## 💻 Usage

1. **Landing Page** (`/`) — View a live feed of recent earthquakes and active cyclones worldwide
2. **Search** — Enter a location name (e.g., "Tokyo", "California") or coordinates to geocode
3. **Dashboard** (`/dashboard`) — Run disaster impact analysis on any location with interactive Leaflet map
4. **Analysis** — View damage zones, nearby resources, rescue team recommendations, and priority score
5. **History** (`/history`) — Browse past analysis reports with sorting and filtering
6. **Analytics** (`/analytics`) — View aggregate statistics and charts of your analyses

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/live-feed` | Recent earthquakes + active cyclones | No |
| `GET` | `/api/geocode?location=...` | Geocode a place name to coordinates | No |
| `GET` | `/api/earthquake?lat=...&lon=...` | Fetch earthquakes near a location | No |
| `GET` | `/api/cyclone?lat=...&lon=...` | Fetch active cyclones | No |
| `GET` | `/api/news?query=...` | Fetch disaster-related news  | No |
| `GET` | `/api/resources?lat=...&lon=...` | Nearby hospitals, fire & police stations | No |
| `GET` | `/api/analyze?lat=...&lon=...&disaster_type=...` | Full impact analysis | No |
| `POST` | `/token` | Login and get JWT access token | No |
| `GET` | `/users/me` | Get current user info | Yes |
| `GET` | `/api/history` | Past analysis logs | Yes |
| `GET` | `/api/stats` | Aggregate analytics stats | Yes |

---

## 🐳 Docker Deployment

### Using Docker Compose (recommended)
```bash
docker-compose up --build
```

### Using Docker directly
```bash
docker build -t pdrdss .
docker run -p 8000:8000 pdrdss
```

The application will be accessible at **http://localhost:8000**

---

## 📄 License

This project is developed as an academic final-year project. All data is sourced from publicly available APIs.

> **Disclaimer:** This system is an academic prototype designed for educational purposes. It should **not** be used as a substitute for certified emergency management systems or professional disaster response tools.
