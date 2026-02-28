# PDRDSS System Architecture

## High-Level Architecture (Corrected)

```mermaid
graph TD
    %% --- Styles ---
    classDef default fill:#ffffff,stroke:#2563eb,stroke-width:2px,rx:10,ry:10;
    classDef highlight fill:#eff6ff,stroke:#1e40af,stroke-width:3px,rx:10,ry:10;
    classDef db fill:#ffffff,stroke:#2563eb,stroke-width:2px,shape:cylinder;
    classDef decision fill:#ffffff,stroke:#2563eb,stroke-width:2px,shape:hexagon;
    classDef ext fill:#f1f5f9,stroke:#64748b,stroke-width:2px,stroke-dasharray: 5 5,rx:5,ry:5;
    classDef terminal fill:#eff6ff,stroke:#2563eb,stroke-width:2px,shape:stadium;

    %% --- Nodes ---
    
    %% User & Frontend
    User([User / Responder]):::terminal
    FE(Frontend Dashboard):::highlight
    
    %% Internal Network / Backend
    subgraph PDRDSS_System [PDRDSS Cloud System]
        direction TB
        Orch(Service Orchestrator):::default
        Auth(Auth Service):::default
        Scoring{{Scoring Engine}}:::decision
        DB[(SQLite DB)]:::db
        
        %% Machine Learning Clusterr
        subgraph AI_Core [AI / ML Core]
            direction LR
            ML_Sev(Severity Models):::default
            ML_Res(Resource Forecaster):::default
            ML_NLP(News NLP):::default
            ML_Anom(Anomaly Detector):::default
            ML_Grok(Grok AI Report):::default
        end
    end

    %% External Internet
    subgraph Internet [External APIs]
        direction LR
        USGS(USGS Quakes):::ext
        NOAA(NOAA Cyclones):::ext
        GDELT(GDELT News):::ext
        OSM(OpenStreetMap):::ext
    end

    %% --- Edges ---
    User <==> FE
    FE <==> Orch
    
    Orch --> Auth
    Orch <--> DB
    Orch -- "Prepare Data" --> Scoring
    
    %% ML Connections
    Scoring -.-> ML_Sev & ML_NLP
    Orch -.-> ML_Res & ML_Anom & ML_Grok
    
    %% Data Ingestion
    Orch -- "Fetch Live Data" --> USGS & NOAA & GDELT & OSM
    
    %% Output
    Scoring ==> Output([Priority Score & Plan]):::terminal
    
    linkStyle default stroke:#2563eb,stroke-width:2px,fill:none;
```

## Component Details

### 1. Frontend Layer
- **Landing Page**: Real-time visualization of USGS earthquakes and NOAA cyclones.
- **Dashboard**: Main command center for running specific disaster analyses.
- **History/Analytics**: Reviewing past logs and aggregated statistics.

### 2. AI/ML Core (`ml_models/`)
This is the system's intelligence engine, replacing hardcoded rules:
- **Severity Classifiers (RandomForest)**: Two separate models for Earthquakes (Mag/Depth) and Cyclones (Wind/Pressure).
- **Resource Forecaster (GradientBoosting)**: 10 regression models predicting specific relief item quantities based on severity and population.
- **News Urgency (DistilBERT)**: Zero-shot NLP classification of disaster news.
- **Anomaly Detection (IsolationForest)**: Unsupervised learning to flag statistical outliers in live feeds.
- **Grok AI (LLM)**: Generates human-readable situation reports via external API.

### 3. Backend Services
- **FastAPI**: Async request handling.
- **Scoring Engine**: Computes weighted priority: `0.4*Severity + 0.3*Pop + 0.2*Res + 0.1*News`.
- **Orchestration**: Aggregates data from 5+ external sources in parallel using `httpx`.
