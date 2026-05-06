# 🌍 PDRDSS — Post-Disaster Rescue Decision Support System

> **AI-powered real-time disaster intelligence platform** that aggregates live earthquake and cyclone data, applies machine learning models, and generates Grok AI situation reports to assist emergency responders with data-driven rescue prioritization.

⚠️ **Academic Prototype** — This is a final-year project and is *not* a certified emergency management tool.

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML%20Models-orange?logo=scikit-learn)](https://scikit-learn.org)
[![Grok AI](https://img.shields.io/badge/Grok-xAI%20LLM-black)](https://x.ai)

---

## 📋 Table of Contents

- [Features](#-features)
- [AI/ML Models](#-aiml-models)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Scoring Engine](#-scoring-engine)
- [Data Sources & APIs](#-data-sources--apis)
- [Project Structure](#-project-structure)
- [Documentation & Research](#-documentation--research)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Docker Deployment](#-docker-deployment)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Live Disaster Feed** | Real-time earthquake (USGS) and cyclone (NOAA NHC) data on an interactive dark map |
| **Dedicated Earthquake Tracker** | Full-featured earthquake monitoring page with real-time USGS data and interactive map |
| **Dedicated Cyclone Tracker** | Full-featured cyclone monitoring page with NOAA NHC data and wind field visualization |
| **Disaster Type Selection** | Clean selection interface to choose between earthquake and cyclone analysis workflows |
| **ML Severity Classification** | RandomForest classifiers predict earthquake & cyclone severity from raw sensor data |
| **NLP News Urgency** | DistilBERT zero-shot classifier scores news article urgency (replaces keyword counting) |
| **ML Resource Forecasting** | GradientBoosting models predict demand for 10 resource types based on severity & population |
| **Grok AI Situation Reports** | xAI Grok LLM generates a 2–3 paragraph expert situation assessment for each analysis |
| **Anomaly Detection** | IsolationForest flags statistically unusual earthquake & cyclone events in the live feed |
| **Geocoding & Search** | Search any location by name or coordinates with confidence scoring |
| **Population Exposure** | Circular impact zone population estimation using WorldPop density data |
| **Resource Mapping** | Nearby hospitals, fire stations & police via OpenStreetMap Overpass API |
| **Damage Zone Visualization** | GeoJSON epicentral / moderate / light damage zones on Leaflet map |
| **Priority Scoring** | Weighted 0–100 rescue priority score combining all ML-derived inputs |
| **Wind Field Visualization** | Cyclone 34/50/64 kt wind radii polygons on map |
| **User Authentication** | JWT-based login with role-based access (admin/user) |
| **Analysis History** | Logged past analyses with filtering, sorting, and analytics dashboard |
| **Dark Emergency Theme** | Professional dark UI optimized for EOC readability |
| **Docker Support** | Containerized deployment with Docker Compose |

---

## 🤖 AI/ML Models

PDRDSS integrates **5 AI/ML models** — implemented as separate, independently trained scikit-learn models in the `ml_models/` package.

### Model 1 — Earthquake Severity Classifier (RandomForest)

**File:** `ml_models/train_severity_classifier.py` → saves `ml_models/severity_model.pkl`  
**Evaluation:** `ml_models/evaluate_severity_classifier.py` → outputs confusion matrix, per-class metrics  
**ROC Analysis:** `ml_models/roc_curve_analysis.py` → generates ROC curves with AUC scores  
**Integration:** `scoring_engine.py` → `predict_severity(magnitude, depth_km, tsunami_flag)`

| Metric | Value |
|---|---|
| Algorithm | `RandomForestClassifier` (120 estimators) |
| Features | Magnitude, depth (km), tsunami flag |
| Classes | CATASTROPHIC · SEVERE · MODERATE · MINOR |
| Accuracy | **93%** on held-out test set |
| ROC-AUC | **0.9947** macro-average |

- Replaces hardcoded `if mag >= 7.0` threshold rules
- A shallow M6.5 with a tsunami flag correctly escalates to CATASTROPHIC
- **Fallback:** rule-based Richter thresholds if model unavailable

---

### Model 1b — Cyclone Severity Classifier (RandomForest)

**File:** `ml_models/train_cyclone_severity_classifier.py` → saves `ml_models/cyclone_severity_model.pkl`  
**Integration:** `scoring_engine.py` → `predict_cyclone_severity(intensity_kt, pressure_hpa, intensification_rate)`

| Metric | Value |
|---|---|
| Algorithm | `RandomForestClassifier` (120 estimators) |
| Features | Wind speed (kt), central pressure (hPa), intensification rate (kt/6h) |
| Classes | CATASTROPHIC · SEVERE · MODERATE · MINOR · NONE |
| Accuracy | **93%** on held-out test set |

- Replaces single-variable Saffir-Simpson threshold rules
- Pressure and intensification rate improve Cat 4/5 detection beyond wind alone
- Dashboard shows Saffir-Simpson category, wind speed in kt/km/h/mph, gradient intensity bar
- **Fallback:** standard Saffir-Simpson thresholds if model unavailable

---

### Model 2 — NLP News Urgency Classifier (DistilBERT)

**File:** `ml_models/news_classifier.py`  
**Integration:** `scoring_engine.py` → `calculate_news_urgency(articles)`

| Metric | Value |
|---|---|
| Model | `typeform/distilbert-base-uncased-mnli` (HuggingFace) |
| Method | Zero-shot classification pipeline |
| Labels | `"urgent life-threatening disaster"` · `"moderate disaster concern"` · `"routine news"` |
| Download | ~250 MB (auto-cached on first run) |

- Replaces a simple keyword-counting loop
- **Fallback:** keyword-based scoring if model unavailable or download fails

---

### Model 3 — Resource Demand Forecaster (GradientBoosting)

**File:** `ml_models/train_resource_forecaster.py` → saves `ml_models/resource_model.pkl`  
**Integration:** `services.py` → `predict_resource_demand(severity, population, disaster_type)`

| Metric | Value |
|---|---|
| Algorithm | `GradientBoostingRegressor` × 10 (one per resource type) |
| Features | Severity code, log-population, disaster type (earthquake/cyclone) |
| Resources Predicted | Water · Shelter · Medical · SAR · Comms · Generators · Food · Blankets · First Aid · Vehicles |
| R² Score | **0.979–0.986** across all 10 resource models |

- Replaces static WHO/Sphere Standards lookup table
- Quantities labelled with `"source": "ML-GradientBoosting"` in API response
- **Fallback:** WHO/Sphere rules-based table if model unavailable

---

### Model 4 — Grok AI Situation Report (xAI LLM)

**Integration:** `services.py` → `get_ai_analysis()` called inside `analyze_disaster_impact()`

| Property | Value |
|---|---|
| Provider | xAI (Grok) |
| Model | `grok-3-mini` |
| Endpoint | `https://api.x.ai/v1/chat/completions` |
| Config | `GROK_API_KEY` in `config.py` |

- Generates a **2–3 paragraph expert situation assessment** per analysis
- Context passed: severity, population, event data, resource counts, rescue teams
- Dashboard renders this as a **🤖 AI Situation Report** panel after the News section
- Includes ethical disclaimer: *"AI-generated assessment — for decision support only"*
- **Fallback:** graceful error message if API call fails

---

### Model 5 — Anomaly Detection for Earthquakes (IsolationForest)

**File:** `ml_models/anomaly_detector.py`  
**Integration:** `services.py` → `get_live_feed_data()` — runs on every earthquake event batch

| Property | Value |
|---|---|
| Algorithm | `IsolationForest` (unsupervised, no pre-training) |
| Features | Magnitude, depth (km), significance score |
| Contamination | 10% (expects ~1 in 10 to be anomalous) |

- Fits on the *live batch* each time — catches current-session outliers
- Flagged events show **⚠ UNUSUAL** amber badge in the Recent Events table
- Badge includes human-readable note: *"unusually high magnitude", "extremely shallow depth"*

---

### Model 5b — Anomaly Detection for Cyclones (IsolationForest)

**File:** `ml_models/cyclone_anomaly_detector.py`  
**Integration:** `services.py` → `get_live_feed_data()` — runs on cyclone events parallel to Model 5

| Property | Value |
|---|---|
| Algorithm | `IsolationForest` (unsupervised) |
| Features | Wind speed (kt), estimated central pressure (hPa) |
| Contamination | 15% |

- Flags extreme storms: *"extreme wind speed (155 kt), extremely low pressure (900 hPa), rapid intensification pattern"*
- Same **⚠ UNUSUAL** amber badge in live feed table

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
| **scikit-learn** | ML models (RandomForest, GradientBoosting, IsolationForest) |
| **joblib** | Model serialization (.pkl files) |
| **transformers** | HuggingFace NLP pipeline (DistilBERT zero-shot) |
| **torch** | PyTorch backend for transformers |

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
| **OpenStreetMap Overpass** | Nearby emergency resources |
| **Nominatim (OSM)** | Geocoding — place name to coordinates |
| **xAI Grok API** | LLM-generated situation reports |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ Landing  │  │Dashboard │  │ History  │  │   Analytics   │   │
│  │  + Map   │  │  + ML UI │  │   Logs   │  │    Charts     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │Earthquake│  │ Cyclone  │  │  Select  │                      │
│  │ Tracker  │  │ Tracker  │  │  Page    │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
└───────┴─────────────┴─────────────┴────────────────┴────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────────────┐ │
│  │  Routes  │  │ Services │  │         ML Models Package       │ │
│  │ (API)    │→ │ (Logic)  │→ │  ┌─────────┐  ┌─────────────┐  │ │
│  └──────────┘  └──────────┘  │  │Severity │  │  Resource   │  │ │
│  ┌──────────┐  ┌──────────┐  │  │Classif. │  │ Forecaster  │  │ │
│  │  Auth    │  │ Scoring  │  │  │(RF×2)   │  │ (GBR×10)    │  │ │
│  │  (JWT)   │  │  Engine  │  │  └─────────┘  └─────────────┘  │ │
│  └──────────┘  └──────────┘  │  ┌─────────┐  ┌─────────────┐  │ │
│                               │  │DistilBERT  │ Anomaly Det.│  │ │
│                               │  │  NLP    │  │ (IsoForest) │  │ │
│                               │  └─────────┘  └─────────────┘  │ │
│                               └────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Async HTTP (httpx)
    ┌─────────────────┼─────────────────────────┐
    ▼                 ▼                          ▼
┌────────┐     ┌──────────┐             ┌──────────────────┐
│  USGS  │     │   NOAA   │             │  GDELT / OSM /   │
│Seismic │     │ Cyclones │             │  xAI Grok API    │
└────────┘     └──────────┘             └──────────────────┘
```

---

## 📊 Scoring Engine

The priority scoring engine uses a **weighted multi-factor formula** to produce a 0–100 rescue priority score. All inputs are now **ML-derived**:

```
Score = (0.4 × Severity) + (0.3 × Population) + (0.2 × Resource Distance) + (0.1 × News Urgency)
```

| Factor | Weight | Source | ML Model |
|---|---|---|---|
| **Severity** | 40% | Strongest event | RandomForest classifier |
| **Population Exposure** | 30% | WorldPop log₁₀ | Rule-based (geo) |
| **Resource Distance** | 20% | Nearest OSM resource | Rule-based (geo) |
| **News Urgency** | 10% | GDELT articles | DistilBERT NLP |

### Priority Labels

| Score | Label |
|---|---|
| 85–100 | 🔴 **CRITICAL** |
| 60–84 | 🟠 **HIGH** |
| 30–59 | 🟡 **MEDIUM** |
| 0–29 | 🟢 **LOW** |

---

## 🔌 Data Sources & APIs

| Source | Type | Endpoint | Data Used |
|---|---|---|---|
| **USGS** | REST API | `earthquake.usgs.gov/fdsnws/event/1/query` | Real-time seismic events (magnitude, depth, coordinates, tsunami flag) |
| **NOAA NHC** | GIS JSON | `www.nhc.noaa.gov/gis/` | Active cyclone advisories (wind speed, pressure, track, wind radii) |
| **GDELT DOC 2.0** | REST API | `api.gdeltproject.org/api/v2/doc/doc` | Real-time disaster news articles for NLP urgency scoring |
| **OpenStreetMap Overpass** | REST API | `overpass-api.de/api/interpreter` | Nearby hospitals, fire stations, police stations |
| **Nominatim (OSM)** | REST API | `nominatim.openstreetmap.org/search` | Forward geocoding (place name → lat/lon) |
| **WorldPop** | Raster Data | Population density grid | Estimated population within impact zones |
| **xAI Grok** | REST API | `api.x.ai/v1/chat/completions` | LLM-generated situation reports (grok-3-mini) |

---

## 📁 Project Structure

```
PRDSSS/
├── main.py                  # FastAPI app entry point & frontend routes
├── routes.py                # API route definitions
├── services.py              # Core business logic, external API integration, ML calls
├── scoring_engine.py        # Multi-factor priority scoring + ML severity predictors
├── models.py                # SQLAlchemy ORM models (User, AnalysisLog, Cache)
├── database.py              # Async database engine & session factory
├── auth.py                  # JWT authentication & password hashing
├── config.py                # Configuration constants, API keys, resource definitions
├── utils.py                 # Caching, HTTP helpers, geospatial utilities
├── routing_service.py       # Distance formatting & routing helpers
├── background_tasks.py      # Background task scheduling
├── create_admin.py          # Admin user creation script
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Container orchestration
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
│
├── ARCHITECTURE.md              # System architecture diagrams
├── ARCHITECTURE_EXPLANATION.md  # Detailed architecture documentation
├── results_discussion.md        # Results & Discussion (research paper section)
├── eda_section_draft.md         # Exploratory Data Analysis draft
│
├── ml_models/                   # 🤖 AI/ML Model Package
│   ├── __init__.py
│   ├── train_severity_classifier.py         # Train earthquake severity RF model
│   ├── train_cyclone_severity_classifier.py # Train cyclone severity RF model
│   ├── train_resource_forecaster.py         # Train resource demand GBR models
│   ├── evaluate_severity_classifier.py      # Evaluation metrics & confusion matrix
│   ├── roc_curve_analysis.py                # ROC curve generation & AUC analysis
│   ├── export_datasets.py                   # Export synthetic training datasets to CSV
│   ├── news_classifier.py                   # DistilBERT NLP urgency wrapper
│   ├── anomaly_detector.py                  # IsolationForest for earthquakes
│   ├── cyclone_anomaly_detector.py          # IsolationForest for cyclones
│   ├── severity_model.pkl                   # Trained earthquake classifier
│   ├── cyclone_severity_model.pkl           # Trained cyclone classifier
│   ├── resource_model.pkl                   # Trained resource forecaster (10 models)
│   ├── earthquake_severity_dataset.csv      # Earthquake training data (exported)
│   ├── cyclone_severity_dataset.csv         # Cyclone training data (exported)
│   └── resource_demand_dataset.csv          # Resource demand training data (exported)
│
├── static/                      # Frontend assets
│   ├── index.html               # Landing page with live disaster feed
│   ├── select.html              # Disaster type selection page
│   ├── earthquake.html          # Dedicated earthquake tracker & dashboard
│   ├── cyclone.html             # Dedicated cyclone tracker & dashboard
│   ├── dashboard.html           # Analysis dashboard with interactive map
│   ├── login.html               # User authentication page
│   ├── history.html             # Past analysis logs viewer
│   ├── analytics.html           # Analytics charts & statistics
│   ├── css/
│   │   ├── landing.css          # Landing page styles
│   │   ├── select.css           # Selection page styles
│   │   └── style.css            # Dashboard & global styles
│   └── js/
│       ├── landing.js           # Live feed, search & map logic
│       ├── earthquake-landing.js # Earthquake tracker page logic
│       ├── cyclone-landing.js   # Cyclone tracker page logic
│       ├── app.js               # Dashboard map, ML analysis rendering
│       ├── auth.js              # Token management & auth helpers
│       ├── history.js           # History page logic
│       └── analytics.js        # Chart rendering & stats
│
├── eda_*.png                    # EDA visualizations (confusion matrix, ROC, histograms, etc.)
├── roc_curve_severity.png       # ROC curve plot from model evaluation
├── *_diagram.jpg                # System architecture & UML diagrams
└── draw_*.py                    # Diagram generation scripts
```

---

## 📄 Documentation & Research

The repository includes research documentation and evaluation artifacts:

| File | Description |
|---|---|
| `ARCHITECTURE_EXPLANATION.md` | Detailed system architecture documentation with component descriptions |
| `results_discussion.md` | Results & Discussion section — cross-validation performance, per-class analysis, ROC curves, feature importance |
| `eda_section_draft.md` | Exploratory Data Analysis section draft |

### EDA Visualizations

| Visualization | File |
|---|---|
| Confusion Matrix | `eda_confusion_matrix.png` |
| ROC Curve (One-vs-Rest) | `eda_roc_curve.png`, `roc_curve_severity.png` |
| Feature Importance | `eda_feature_importance.png` |
| Earthquake Magnitude Distribution | `eda_earthquake_magnitude_histogram.png` |
| Earthquake Class Distribution | `eda_earthquake_class_distribution.png` |
| Cyclone Windspeed Distribution | `eda_cyclone_windspeed_histogram.png` |
| Comparative Analysis | `eda_comparative_analysis.png` |
| True vs Predicted Line Graph | `eda_line_graph.png` |

### Architecture Diagrams

| Diagram | File |
|---|---|
| Functional Block Diagram | `pdrdss_functional_block_diagram.jpg` |
| Detailed Block Diagram | `pdrdss_detailed_block_diagram.jpg` |
| AI/ML Core Diagram | `aiml_core_diagram.jpg` |
| Data Flow Diagram | `data_flow_diagram.jpg` |
| Service Orchestrator | `service_orchestrator_diagram.jpg` |
| UML Class Diagram | `uml_class_diagram.jpg` |
| UML Use Case Diagram | `uml_use_case.jpg` |

---

## 🚀 Installation

### Prerequisites
- **Python 3.9+**
- **pip** (Python package manager)
- **Git**

> ⚠️ **Note:** The `transformers` package (DistilBERT) requires ~2 GB disk space for PyTorch. The model (~250 MB) downloads automatically on first use and is cached locally.

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

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROK_API_KEY
   ```

5. **Train the ML models** (one-time setup — takes ~30 seconds)
   ```bash
   python ml_models/train_severity_classifier.py
   python ml_models/train_cyclone_severity_classifier.py
   python ml_models/train_resource_forecaster.py
   ```
   > The trained `.pkl` files are already committed to the repository, so this step is only needed if you delete them.

6. **Create an admin user** (optional — for authenticated features)
   ```bash
   python create_admin.py
   ```

7. **Run the application**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   The server starts at **http://localhost:8000**

---

## 💻 Usage

1. **Landing Page** (`/`) — View real-time earthquake tracker and active cyclone feed
2. **Select Disaster Type** (`/select`) — Choose between earthquake or cyclone analysis
3. **Earthquake Tracker** (`/earthquake`) — Dedicated earthquake monitoring with real-time USGS data
4. **Cyclone Tracker** (`/cyclone`) — Dedicated cyclone monitoring with NOAA NHC data
5. **Search** — Enter a location name (e.g., "Tokyo", "Mumbai") or coordinates (lat, lon)
6. **Dashboard** (`/dashboard`) — Run ML-powered disaster impact analysis on any location
7. **Analysis Panels** — View:
   - ML-predicted severity (with model label)
   - Damage zones on interactive Leaflet map
   - ML-forecasted resource requirements (10 types)
   - Rescue team recommendations
   - 🤖 Grok AI situation report
   - ⚠ Anomaly badges on unusual events
8. **History** (`/history`) — Browse past analysis reports
9. **Analytics** (`/analytics`) — View aggregate statistics and charts

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/live-feed` | Recent earthquakes + cyclones with anomaly flags | No |
| `GET` | `/api/geocode?location=...` | Geocode a place name to coordinates | No |
| `GET` | `/api/earthquake?lat=...&lon=...` | Fetch earthquakes near a location | No |
| `GET` | `/api/cyclone?lat=...&lon=...` | Fetch active cyclones | No |
| `GET` | `/api/news?query=...` | Fetch disaster-related news | No |
| `GET` | `/api/resources?lat=...&lon=...` | Nearby hospitals, fire & police stations | No |
| `GET` | `/api/analyze?lat=...&lon=...&disaster_type=...` | Full ML-powered impact analysis + Grok AI report | No |
| `POST` | `/token` | Login and get JWT access token | No |
| `GET` | `/users/me` | Get current user info | Yes |
| `GET` | `/api/history` | Past analysis logs | Yes |
| `GET` | `/api/stats` | Aggregate analytics stats | Yes |

### Sample `/api/analyze` Response (AI/ML fields)

```json
{
  "severity": "CATASTROPHIC",
  "priority_score": 91.4,
  "allocated_resources": [
    { "name": "Water Purification Units", "quantity": 42, "source": "ML-GradientBoosting" }
  ],
  "ai_analysis": {
    "available": true,
    "summary": "The M7.8 earthquake near Adana poses an extreme humanitarian crisis...",
    "model": "grok-3-mini"
  },
  "recent_events": [
    { "magnitude": 7.8, "is_anomaly": true, "anomaly_note": "unusually high magnitude" }
  ]
}
```

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
