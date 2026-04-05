# PDRDSS — Architecture Diagram Explanation

This document provides a detailed explanation of every term and word used in the PDRDSS System Architecture Diagram.

---

## TOP ROW — User Interface Components

---

### 1. User

The **User** represents the person who uses this system. In our case, the user is an **emergency responder**, **disaster relief coordinator**, or **government official** who needs to quickly assess the impact of a natural disaster (earthquake or cyclone) and make rescue decisions. The user accesses the system through a web browser on their computer or phone.

---

### 2. Dashboard

The **Dashboard** is the main analysis page of the application. It is the **command center** where the user performs disaster impact analysis. The user enters a location (e.g., "Tokyo", "California"), selects a disaster type (Earthquake or Cyclone), and clicks "Analyze." The system then displays:

- Severity level (MINOR / MODERATE / SEVERE / CATASTROPHIC)
- Priority score (0–100)
- Damage zone map with impact circles
- Nearby hospitals, fire stations, and police stations
- Recommended rescue teams and resource allocation
- AI-generated situation report
- Real-time related news articles

The dashboard file is `dashboard.html` in the project.

---

### 3. Landing Page

The **Landing Page** is the first page the user sees when they open the website. It shows a **live interactive map** displaying real-time earthquake and cyclone events happening around the world right now. Earthquake markers show magnitude, location, and time. Cyclone markers show storm name, wind speed, and category. Users can click on any event to navigate to the Dashboard for detailed analysis.

The landing page file is `index.html` in the project.

---

### 4. Login

The **Login** page is where users authenticate themselves by entering their **username** and **password**. After successful login, the server returns a **JWT token** (explained below under Auth) that the browser stores and uses for all future requests. This ensures only authorized users can access protected features like history and analytics.

The login page file is `login.html` in the project.

---

## APPLICATION LAYER

---

### What is "Application Layer"?

The **Application Layer** is the **backend** of the system — the server-side code that runs on the server machine (not on the user's browser). It is the **brain** of the system. It contains all the business logic: receiving requests from the frontend, processing data, calling AI models, fetching data from external sources, computing scores, and sending back results. The user never sees this layer directly — they only interact with it through the frontend pages.

---

### 5. Fast API Server

**FastAPI** is a modern, high-performance **Python web framework** used to build the backend server of our application. It:

- Receives **HTTP requests** from the frontend (user's browser)
- Processes them by calling the appropriate functions
- Returns **JSON responses** back to the frontend
- Supports **asynchronous (async)** programming, meaning it can handle multiple user requests at the same time without waiting for one to finish before starting another — this makes the system fast
- Runs on top of **Uvicorn**, which is the actual web server that listens for incoming network connections on port 8000

In our project, the FastAPI server is defined in `main.py`.

---

### 6. Router

The **Router** is the component that **maps each URL (endpoint) to a specific Python function**. When a request comes from the frontend (e.g., the browser calls `/api/earthquake`), the router determines which function should handle that request and calls it.

Our router defines the following API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/api/live-feed` | Returns real-time earthquake and cyclone data for the landing page |
| `/api/analyze` | Runs the full disaster impact analysis |
| `/api/earthquake` | Fetches earthquake data near a specific location from USGS |
| `/api/cyclone` | Fetches active cyclone data from NOAA |
| `/api/news` | Fetches disaster-related news articles from GDELT |
| `/api/resources` | Fetches nearby hospitals, fire stations, police from OpenStreetMap |
| `/api/geocode` | Converts a place name (e.g., "Tokyo") to latitude/longitude coordinates |
| `/api/history` | Returns past analysis logs for the logged-in user |
| `/api/stats` | Returns aggregated statistics for the analytics page |
| `/token` | Login endpoint — verifies credentials and returns a JWT token |

In our project, the router is defined in `routes.py`.

---

### 7. Service Orchestrator

The **Service Orchestrator** is the **central coordinator** of all backend operations. When a user clicks "Analyze" on the dashboard, the Service Orchestrator handles the entire process:

1. Fetches earthquake or cyclone data from USGS/NOAA
2. Fetches nearby hospitals, fire stations, and police from OpenStreetMap
3. Fetches disaster-related news from GDELT
4. Fetches current weather conditions from Open-Meteo
5. Runs the **Severity Classifier** ML model to determine disaster severity
6. Estimates **population exposure** using WorldPop density data
7. Runs the **Resource Forecaster** ML model to predict relief resource quantities
8. Sends data to the **Scoring Engine** to compute the Priority Score
9. Calls **Grok LLM** to generate a human-readable situation report
10. Bundles all the results together and returns them to the frontend

The word "Orchestrator" means a conductor or coordinator — just like an orchestra conductor coordinates all the musicians, the Service Orchestrator coordinates all the different services and models.

It performs many of these tasks **in parallel** (at the same time) using Python's `asyncio` and the `httpx` library, making the analysis faster.

In our project, the Service Orchestrator is defined in `services.py`.

---

### 8. REST API

**REST API** stands for **RE**presentational **S**tate **T**ransfer **A**pplication **P**rogramming **I**nterface.

- **API** = A set of rules and endpoints that allows two software systems to communicate with each other
- **REST** = An architectural style for designing APIs that uses standard HTTP methods (GET, POST, PUT, DELETE)

In our system, the REST API is the communication bridge between the **frontend** (browser) and the **backend** (FastAPI server). The frontend sends HTTP requests to specific URLs (endpoints), and the backend returns data in **JSON format** (a lightweight text format for structured data).

Example:
- Frontend sends: `GET /api/analyze?lat=35.6&lon=139.7&disaster_type=earthquake`
- Backend responds with JSON: `{"severity": "SEVERE", "priority_score": 72.5, ...}`

---

### 9. Auth (JWT)

**Auth** stands for **Authentication** — the process of verifying who the user is (confirming their identity).

**JWT** stands for **JSON Web Token** — a compact, digitally signed token (a long encrypted string) that the server creates after the user successfully logs in. This token contains:
- The username
- An expiration time
- A digital signature (to prevent tampering)

After login, the browser stores this token and sends it with every subsequent request. The server checks the token to verify the user is authenticated — this way, the user doesn't need to send their password with every request.

Our system also uses:
- **OAuth2** — An industry-standard protocol for handling authentication flows. We use the "Password Flow" where the user sends username + password and receives a token.
- **PBKDF2** (Password-Based Key Derivation Function 2) — A secure hashing algorithm used to store passwords. We never store the actual password in the database — we store a **one-way hash** (an irreversible scrambled version). When the user logs in, we hash the entered password and compare it with the stored hash.

In our project, authentication is handled in `auth.py`.

---

### 10. Config

**Config** stands for **Configuration** — a module that stores all the **settings, constants, and configuration values** used across the entire application. Instead of hardcoding values in multiple files, we keep them in one central place so they're easy to find and change.

The Config module contains:
- **HTTP_TIMEOUT** — Maximum time (20 seconds) to wait for an external API response
- **CACHE_TTL** — How long cached data stays valid (300 seconds = 5 minutes)
- **POPULATION_DENSITY** — A lookup table of population density per country (persons per km²), sourced from WorldPop 2020 data
- **RESOURCE_TYPES** — A list of 10 relief resource items (water, shelters, medical, etc.)
- **SECRET_KEY** — The secret key used to sign JWT tokens
- **GROK_API_KEY** — The API key for accessing the xAI Grok LLM service
- **GROK_MODEL** — The specific Grok model to use (grok-3-mini)

In our project, the configuration is defined in `config.py`.

---

### 11. Background Task

A **Background Task** is a process that runs **automatically and continuously in the background** without any user interaction. It operates independently of user requests.

In our system, the background task runs in an infinite loop, executing every **5 minutes** to:
1. Fetch the latest earthquake data from the **USGS API**
2. Fetch the latest cyclone data from the **NOAA API**
3. Store the fetched data in the **SQLite Database** (`disaster_cache` table)

This ensures the database always has fresh, up-to-date disaster data, even when no user is actively using the system. When a user opens the landing page, the data is already available.

In our project, the background task is defined in `background_tasks.py`.

---

### 12. Cache (TTL)

**Cache** is a **temporary storage** mechanism that saves the results of expensive or slow operations (like external API calls). If the same data is requested again shortly after, the cached result is returned instantly without repeating the expensive operation.

**TTL** stands for **Time To Live** — the duration for which a cached item remains valid before it expires and must be refreshed. In our system, TTL = **300 seconds (5 minutes)**.

Example: If User A searches for earthquakes near Tokyo, the system calls the USGS API and caches the result. If User B searches the same area 2 minutes later, the system returns the cached result instantly without calling USGS again. After 5 minutes, the cache expires, and the next request will fetch fresh data.

This improves **performance** (faster responses) and **reduces load** on external APIs (fewer redundant calls).

In our project, the caching logic is implemented in `utils.py`.

---

## ML MODELS

---

### What is "ML Models"?

**ML** stands for **Machine Learning** — a branch of Artificial Intelligence (AI) where computer algorithms **learn patterns from data** and make predictions or decisions without being explicitly programmed for every possible scenario. Instead of writing fixed rules like "if magnitude > 7.0, then CATASTROPHIC," we train a model on thousands of historical earthquake records, and the model learns the patterns itself.

**Models** refers to the trained ML algorithms stored as `.pkl` (pickle) files. Once trained, these models can make instant predictions on new, unseen data.

---

### 13. Scoring Engine

The **Scoring Engine** is a mathematical component that computes a **Priority Score** — a single number between 0 and 100 that tells the responder how urgent the disaster situation is. It combines multiple factors using a **weighted formula**:

```
Priority Score = (0.4 × Severity) + (0.3 × Population) + (0.2 × Resource Distance) + (0.1 × News Urgency)
```

Breaking down each factor:
- **Severity (40% weight)** — How severe is the disaster? Converted to a numeric scale: CATASTROPHIC = 100, SEVERE = 80, MODERATE = 50, MINOR = 20
- **Population (30% weight)** — How many people are in the affected area? Uses a logarithmic scale to handle large numbers
- **Resource Distance (20% weight)** — How far is the nearest hospital or fire station? Farther distance = higher urgency (less accessible help)
- **News Urgency (10% weight)** — How alarming are the news headlines? Determined by NLP analysis

The final score is classified into priority labels:
- **CRITICAL** (score ≥ 85) — Immediate action required
- **HIGH** (score ≥ 60) — Urgent attention needed
- **MEDIUM** (score ≥ 30) — Monitor and prepare
- **LOW** (score < 30) — Low risk situation

In our project, the Scoring Engine is defined in `scoring_engine.py`.

---

### 14. Priority Score

The **Priority Score** is the **output** of the Scoring Engine — a numerical value from **0 to 100** that quantifies how urgent and severe a disaster situation is. It combines severity, population exposure, resource accessibility, and news urgency into one actionable number. A higher score means the disaster requires more immediate attention and resource deployment.

---

### 15. Severity Classifier

The **Severity Classifier** is a machine learning model that predicts the **severity level** of an earthquake. It takes 3 input features:
- **Magnitude** — The strength of the earthquake (e.g., 6.5 on the Richter scale)
- **Depth** — How deep below the Earth's surface the earthquake occurred (in km). Shallower earthquakes cause more surface damage
- **Tsunami flag** — Whether a tsunami warning was issued (1 = yes, 0 = no)

It outputs one of four categories: **CATASTROPHIC**, **SEVERE**, **MODERATE**, or **MINOR**.

The algorithm used is **RandomForest** — an ensemble (group) of many **decision trees**. Each tree is trained on a random subset of the training data and makes its own prediction. The final answer is determined by **majority voting** — whichever category gets the most votes from all the trees wins. RandomForest is robust, handles noisy data well, and resists overfitting.

The trained model is stored as `severity_model.pkl`. If the model file is unavailable, the system falls back to simple rule-based thresholds (e.g., magnitude ≥ 7.0 = CATASTROPHIC).

In our project, this is implemented in `scoring_engine.py` and trained via `ml_models/train_severity_classifier.py`.

---

### 16. Resource Forecaster

The **Resource Forecaster** is a machine learning model that predicts **how many relief resources** are needed for a given disaster. It takes 3 inputs:
- **Severity level** (MINOR / MODERATE / SEVERE / CATASTROPHIC)
- **Population count** in the affected area
- **Disaster type** (earthquake or cyclone)

It outputs predicted quantities for **10 different relief items**:
1. Water Purification Units
2. Emergency Shelter Kits
3. Medical Supply Crates
4. SAR (Search and Rescue) Equipment Sets
5. Communication Radios
6. Portable Generators
7. Food Ration Packages
8. Thermal Blankets
9. First Aid Stations
10. Evacuation Vehicles

The algorithm used is **GradientBoosting** — an ensemble method that builds models **sequentially** (one after another). Each new model focuses specifically on correcting the errors made by the previous model. This iterative improvement makes GradientBoosting extremely accurate for predicting numerical values.

There are **10 separate regression models** — one for each resource type — all stored together in `resource_model.pkl`.

In our project, this is implemented in `services.py` and trained via `ml_models/train_resource_forecaster.py`.

---

### 17. News NLP

**NLP** stands for **Natural Language Processing** — a branch of Artificial Intelligence that enables computers to understand, interpret, and analyze **human language** (text). 

The **News NLP** module analyzes disaster-related **news article headlines** and assigns each one an **urgency score** from 0 to 100. Headlines mentioning words like "trapped," "collapse," "tsunami," or "casualties" receive higher urgency scores.

The algorithm used is **DistilBERT** with **Zero-Shot Classification**:
- **BERT** (Bidirectional Encoder Representations from Transformers) is a deep learning model developed by Google that understands the meaning and context of text
- **DistilBERT** is a lighter, faster version of BERT — it retains 97% of BERT's accuracy while being 60% faster and 40% smaller
- **Zero-Shot Classification** means the model can classify text into categories (like "urgent disaster" or "routine update") **without needing to be trained on disaster-specific data** — it generalizes from its pre-training on billions of words

If the NLP model is unavailable, the system falls back to **keyword matching** — a simpler approach that assigns points for specific words found in headlines (e.g., "trapped" = +15 points, "tsunami" = +20 points, "destroyed" = +10 points).

In our project, this is implemented in `ml_models/news_classifier.py`.

---

### 18. Anomaly Detector

The **Anomaly Detector** identifies **unusual or outlier events** in the live earthquake and cyclone data feed. An anomaly is a data point that is significantly different from the majority of the data. For example:
- An earthquake with an unusually high magnitude compared to recent events
- A cyclone with abnormally rapid intensification
- An event with unusual depth or location characteristics

The algorithm used is **IsolationForest** — an **unsupervised** machine learning algorithm (meaning it does not need labeled training data). It works by randomly partitioning (splitting) the data. Anomalies are rare and different from normal data, so they are **easier to isolate** — they need fewer random splits to be separated from the rest. The algorithm measures how quickly a data point gets isolated: faster isolation = more likely an anomaly.

In our project, this is implemented in `ml_models/anomaly_detector.py`.

---

### 19. Groq LLM

**Note:** In the diagram, this appears as "Groq LLM" but the system actually uses **Grok** (by xAI). 

**LLM** stands for **Large Language Model** — a type of AI model trained on massive amounts of text data (billions of words from books, websites, articles) that can understand and generate human-like language.

**Grok** is an LLM developed by **xAI** (Elon Musk's AI company). In our system, Grok receives all the analysis data (severity, population exposure, nearby resources, news headlines) and generates a **natural language situation report** — a comprehensive, human-readable paragraph describing what happened, how severe it is, how many people are affected, and what actions should be taken.

This makes the system's output more accessible and understandable for non-technical emergency responders who may not want to interpret raw numbers and charts.

We use the **Grok-3-mini** model, accessed via the **xAI API** (`https://api.x.ai/v1/chat/completions`).

In our project, this is implemented in the `get_ai_analysis()` function in `services.py`.

---

## DATABASE

---

### 20. Database

The **Database** is the system's **persistent storage** — where all data is saved permanently so it survives even when the server restarts. Our system uses **SQLite**, a lightweight, file-based relational database. Unlike databases like MySQL or PostgreSQL that run as separate server programs, SQLite stores **everything in a single file** called `pdrdss.db`.

We access the database asynchronously (non-blocking) using:
- **aiosqlite** — An async Python wrapper for SQLite
- **SQLAlchemy** — A Python ORM (Object-Relational Mapper) that lets us interact with the database using Python classes and objects instead of writing raw SQL queries

The database contains **4 tables**:

| Table | What it Stores |
|-------|---------------|
| **users** | User accounts — username, hashed password, role (admin/user), creation date |
| **analysis_logs** | Every analysis ever performed — location name, disaster type, severity, priority score, timestamp, user ID |
| **disaster_cache** | Cached raw data from USGS and NOAA — event ID, type (earthquake/cyclone), latitude, longitude, raw JSON data, timestamp |
| **resource_cache** | Cached nearby infrastructure data — latitude, longitude, search radius, JSON data (hospitals, fire stations, police), timestamp |

In our project, the database setup is in `database.py` and the table definitions are in `models.py`.

---

## EXTERNAL APIs

---

### What are "External APIs"?

**External APIs** are third-party web services hosted on the internet that our system calls to fetch **real-time data**. Our system does not generate or fabricate disaster data — it pulls **live, real data** from these trusted public sources via HTTP requests. The word "External" means these services are **outside** our system, maintained by other organizations.

---

### 21. USGS

**USGS** stands for **United States Geological Survey** — a scientific agency of the United States government that studies the landscape, natural resources, and natural hazards of the U.S. and the world. 

We use the **USGS Earthquake Hazards Program API** to fetch real-time earthquake data from around the world, including:
- Magnitude (strength of the earthquake)
- Epicenter location (latitude and longitude)
- Depth (how deep below the surface)
- Time of occurrence
- Tsunami alert status
- Felt reports

The data is updated every few minutes. API URL: `https://earthquake.usgs.gov/fdsnws/event/1/query`

---

### 22. NOAA

**NOAA** stands for **National Oceanic and Atmospheric Administration** — a U.S. government agency that monitors oceans, weather, and atmospheric conditions globally.

We use the **NHC (National Hurricane Center)** data feed from NOAA to get information about **active cyclones and hurricanes**, including:
- Storm name and ID
- Current position (latitude/longitude)
- Maximum sustained wind speed (in knots)
- Central pressure (in hectopascals)
- Storm category (Tropical Depression, Tropical Storm, Hurricane Cat 1–5)
- Movement direction and speed

API URL: `https://www.nhc.noaa.gov/CurrentSummaries.json`

---

### 23. GDELT

**GDELT** stands for **Global Database of Events, Language, and Tone** — one of the largest open databases in the world that monitors **news media** from nearly every country in over 100 languages, updated every 15 minutes.

We use the **GDELT DOC 2.0 API** to fetch recent news articles related to a disaster event. For example, searching "earthquake Turkey" returns news headlines, source URLs, publication dates, and thumbnail images from the last 24 hours. This helps the system assess **media urgency** — how much attention the disaster is getting, and whether reports mention casualties, damage, or rescue operations.

---

### 24. OpenStreetMap

**OpenStreetMap (OSM)** is a free, open-source, community-built map of the entire world — often described as the "Wikipedia of maps." Millions of volunteers worldwide contribute and maintain the map data.

We use the **Overpass API** (a query interface for OpenStreetMap data) to find **nearby critical infrastructure** within a given radius of the disaster location:
- **Hospitals** — for treating injured people
- **Fire stations** — for rescue and firefighting operations
- **Police stations** — for law enforcement and crowd control

This helps responders identify the closest available resources.

---

### 25. Open-Meteo

**Open-Meteo** is a free, open-source **weather API** that provides current and forecast weather data for any location in the world, without requiring an API key.

We use it to fetch **current weather conditions** at the disaster location:
- Temperature
- Wind speed and direction
- Precipitation (rain/snow)
- Humidity

Weather context is important because conditions like heavy rain after an earthquake can cause landslides, and high winds during a cyclone affect rescue operations.

---

### 26. OSRM

**OSRM** stands for **Open Source Routing Machine** — a free, open-source routing engine that calculates the **fastest driving route** between two geographic points on the road network.

We use OSRM to calculate:
- **Driving distance** (in km) from the disaster location to the nearest hospital, fire station, or police station
- **Estimated travel time** (in minutes)

This is more useful than straight-line (aerial) distance because roads may be winding, and some routes may be blocked. OSRM uses actual road network data from OpenStreetMap.

API URL: `http://router.project-osrm.org/route/v1/driving`

---

### 27. Nominatim

**Nominatim** is OpenStreetMap's **geocoding service**. 

**Geocoding** is the process of converting a **place name** (like "Tokyo", "San Francisco", or "Chennai") into **geographic coordinates** (latitude and longitude numbers, like 35.6762, 139.6503).

When the user types a location name in the dashboard search box, Nominatim converts it into coordinates that our system can use to query all the other APIs (USGS, NOAA, OpenStreetMap, etc.). Without geocoding, the user would have to manually enter latitude and longitude numbers.

---

### 28. xAI Grok

**xAI** is an artificial intelligence company founded by Elon Musk. **Grok** is their large language model (LLM).

We use the **xAI Grok API** to send all our analysis data (severity, population, resources, news) and receive back a **natural language situation report** — a human-readable summary paragraph that describes the disaster, its impact, and recommended actions. This is the same component as "Groq LLM" described in the ML Models section above.

API URL: `https://api.x.ai/v1/chat/completions`

---

## CONNECTIONS (Arrows in the Diagram)

The arrows in the architecture diagram represent how data flows between components:

| From | To | What Happens |
|------|----|-------------|
| **User** → **Dashboard / Landing Page / Login** | The user opens web pages in their browser |
| **Frontend** ↔ **FastAPI Server** (via REST API) | The browser sends HTTP requests; the server returns JSON responses |
| **Router** → **Service Orchestrator** | The router receives an API request and delegates it to the Service Orchestrator |
| **Service Orchestrator** → **Scoring Engine** | The orchestrator sends severity, population, distance, and news data to compute the Priority Score |
| **Service Orchestrator** → **ML Models** | The orchestrator calls ML models for severity prediction, resource forecasting, news analysis |
| **Scoring Engine** → **Priority Score** | The scoring engine outputs the calculated priority score |
| **Service Orchestrator** → **Database** | The orchestrator reads cached data from and writes analysis logs to SQLite |
| **Service Orchestrator** → **External APIs** | The orchestrator fetches real-time data from USGS, NOAA, GDELT, OSM, etc. |
| **Background Task** → **Database** | The background task stores periodically fetched data in the disaster_cache table |
| **Background Task** → **External APIs** | The background task calls USGS and NOAA every 5 minutes for fresh data |
| **Auth (JWT)** → **Router** | Authentication middleware checks the JWT token before allowing access |
| **Cache (TTL)** → **Service Orchestrator** | The cache provides previously fetched data if it hasn't expired |

---

## SUMMARY

The PDRDSS architecture consists of three main layers:

1. **Top Row (Frontend)** — What the user sees and interacts with: Dashboard for analysis, Landing Page for live events, Login for authentication.

2. **Application Layer (Backend)** — The core processing engine: FastAPI server receives requests via the Router, the Service Orchestrator coordinates all data fetching and processing, Auth handles security, Background Tasks keep data fresh, and Cache speeds up responses.

3. **ML Models** — The intelligence layer: Scoring Engine computes priority using a weighted formula, Severity Classifier and Resource Forecaster use trained ML models, News NLP analyzes headlines, Anomaly Detector flags outliers, and Grok LLM generates human-readable reports.

4. **Database** — Persistent storage for users, analysis logs, and cached data.

5. **External APIs** — Real-time data sources: USGS (earthquakes), NOAA (cyclones), GDELT (news), OpenStreetMap (infrastructure), Open-Meteo (weather), OSRM (routing), Nominatim (geocoding), and xAI Grok (AI reports).
