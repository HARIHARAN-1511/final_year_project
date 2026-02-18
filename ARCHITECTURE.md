# PDRDSS System Architecture

## Project Overview
The **Post-Disaster Rescue Decision Support System (PDRDSS)** is a real-time disaster management platform. It aggregates live data from global agencies (USGS, NOAA), processes it with local risk algorithms, and provides actionable insights for rescue operations.

## Architecture Diagram
The following diagram illustrates the system's high-level architecture, data flows, and external integrations.

```mermaid
graph TD
    %% Define Black & White Style
    classDef bw fill:#fff,stroke:#000,stroke-width:2px,color:#000;
    classDef dashed fill:none,stroke:#000,stroke-width:1px,stroke-dasharray: 5 5,color:#000;

    %% Client Layer
    User[("Web Browser<br>(HTML/JS Frontend)")]:::bw

    %% Backend Layer
    subgraph "Backend System (FastAPI)"
        direction TB
        API[("API Gateway<br>(routes.py)")]:::bw
        Auth[("Auth Module<br>(auth.py)")]:::bw
        Orchestrator[("Service Aggregator<br>(services.py)")]:::bw
        
        subgraph "Core Engines"
            Scoring[("Scoring Engine<br>(scoring_engine.py)")]:::bw
            Router[("Routing Service<br>(routing_service.py)")]:::bw
        end
        
        CacheWorker[("Background Worker<br>(background_tasks.py)")]:::bw
    end

    %% Data Layer
    subgraph "Persistence"
        DB[("SQLite Database<br>(pdrdss.db)")]:::bw
    end

    %% External Layer
    subgraph "External Data Providers"
        USGS[("USGS API<br>(Earthquakes)")]:::bw
        NOAA[("NOAA API<br>(Cyclones)")]:::bw
        GDELT[("GDELT API<br>(News)")]:::bw
        OSM[("OpenStreetMap<br>(Hospitals/Police)")]:::bw
        Meteo[("Open-Meteo<br>(Weather)")]:::bw
        OSRM[("OSRM Project<br>(Rescue Routing)")]:::bw
    end

    %% Connections
    User -- "HTTP / REST" --> API
    
    API -- "Authenticate" --> Auth
    API -- "Analysis Request" --> Orchestrator
    API -- "Read History" --> DB
    
    Auth -- "Verify User" --> DB

    Orchestrator -- "Calculate Risk" --> Scoring
    Orchestrator -- "Calc Logistics" --> Router
    Orchestrator -- "Log Result" --> DB
    
    %% Service to External
    Orchestrator -- "Fetch Data" --> USGS
    Orchestrator -- "Fetch Data" --> NOAA
    Orchestrator -- "Fetch Data" --> GDELT
    Orchestrator -- "Fetch Data" --> OSM
    Orchestrator -- "Fetch Data" --> Meteo
    
    Router -- "Get Route" --> OSRM

    %% Background Tasks
    CacheWorker -- "Periodic Sync" ----> USGS
    CacheWorker -- "Periodic Sync" ----> NOAA
    CacheWorker -- "Update Cache" -.-> DB

    %% Styling specific links if needed
    linkStyle default stroke:black,stroke-width:1px;
```

## Component Analysis

### 1. Frontend (Presentation Layer)
- **Tech**: HTML5, Vanilla JS, CSS3.
- **Files**: `static/` directory.
- **Role**: Renders the Leaflet map, displays analytics charts, and sends async requests to the backend.

### 2. Backend (Application Layer)
- **Tech**: Python 3.10+, FastAPI.
- **Entry Point**: `main.py` initializes the app and serves static files.
- **Routing**: `routes.py` handles API endpoints (`/api/analyze`, `/api/live-feed`).
- **Logic**: `services.py` acts as the central controller, calling external APIs concurrently and aggregating results.

### 3. Core Logic Engines
- **Scoring Engine** (`scoring_engine.py`): Implements the mathematical models to assign priority scores (0-100) based on severity, population density, and news urgency.
- **Routing Service** (`routing_service.py`): Interfaces with OSRM to calculate realistic driving times for rescue teams, falling back to Haversine distance if needed.

### 4. Data Persistence & Caching
- **Database**: SQLite (via SQLAlchemy + `aiosqlite` for async access).
- **Tables**: `users`, `analysis_logs`, `disaster_cache`, `resource_cache`.
- **Background Tasks**: `background_tasks.py` runs an infinite loop to pre-fetch earthquake and cyclone data into the `DisasterCache` table, ensuring the landing page loads instantly.

### 5. External Integrations
- **USGS & NOAA**: Primary sources for disaster event data.
- **Simple Caching**: `utils.py` implements a simple in-memory TTL mechanism for API calls to avoid rate limits and improve performance.
