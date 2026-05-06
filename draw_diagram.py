import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(16, 18))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

def draw_group(x, y, width, height, text):
    rect = patches.Rectangle((x - width/2, y - height/2), width, height, 
                             linewidth=2, linestyle='--', edgecolor='black', facecolor='none')
    ax.add_patch(rect)
    ax.text(x, y + height/2 + 1, text, ha='center', va='bottom', fontsize=14, color='black', weight='bold')

def draw_block(x, y, width, height, text, bold=True):
    rect = patches.Rectangle((x - width/2, y - height/2), width, height, 
                             linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(rect)
    fw = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=11, color='black', weight=fw)

def draw_arrow(sx, sy, ex, ey):
    ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(facecolor='black', edgecolor='black', shrink=0.02, width=1.5, headwidth=8, headlength=10))

# --- DRAW GROUPS ---
# Application Layer Group
draw_group(50, 68, 70, 18, "Application Layer (Backend)")

# AI & Machine Learning Core Group
draw_group(83, 33, 26, 62, "AI & Machine Learning Core")

# Persistence Layer Group
draw_group(17, 50, 26, 12, "Persistence Layer")

# External APIs Layer Group
draw_group(35, 23, 50, 20, "External APIs & Data Sources")


# --- DRAW BLOCKS ---
bw, bh = 18, 5
blocks = {
    'User / Emergency Responder': (50, 96),
    
    # UI
    'Landing Page\n(Live Events Map)': (28, 86),
    'Dashboard\n(Command Center)': (50, 86),
    'Login / Auth UI': (72, 86),
    
    # Backend
    'Auth (JWT)\n& App Config': (30, 73),
    'FastAPI Server\n& API Router': (50, 73),
    'Background Task\n& TTL Cache': (70, 73),
    'Service Orchestrator\n(Backend Coordinator)': (50, 63),
    
    # DB
    'SQLite Database\n(Users, Logs, Cache)': (17, 50),
    
    # ML Models (X=83)
    'Scoring Engine\n(Priority Score Formula)': (83, 58),
    'Severity Classifier\n(RandomForest, Mag/Depth)': (83, 48),
    'Resource Forecaster\n(GradientBoosting, 10 Items)': (83, 38),
    'News NLP\n(DistilBERT, Urgency)': (83, 28),
    'Anomaly Detector\n(IsolationForest, Outliers)': (83, 18),
    'xAI Grok LLM API\n(Situation Report Generation)': (83, 8),
    
    # External APIs (X=20 and X=50)
    'USGS (Quakes API)\nNOAA (Cyclones API)': (22, 28),
    'GDELT (News Media API)': (22, 18),
    'OpenStreetMap\n& OSRM (Routing API)': (48, 28),
    'Nominatim (Geocoding)\n& Open-Meteo (Weather)': (48, 18),
}

# Custom widths for some blocks
for name, (x, y) in blocks.items():
    current_bw = bw
    if "AI & Machine Learning Core" in name or 'Scoring' in name or 'Severity' in name or 'Forecaster' in name or 'NLP' in name or 'Anomaly' in name or 'Grok' in name:
        current_bw = 24
    if "USGS" in name or "OSM" in name or 'GDELT' in name or 'Nominatim' in name or 'OpenStreetMap' in name:
        current_bw = 22
    if "SQLite" in name:
        current_bw = 24

    draw_block(x, y, current_bw, bh, name)

# --- DRAW ARROWS ---
# User to Interfaces
draw_arrow(50, 93.5, 50, 88.5) # User to Dashboard
draw_arrow(49, 93.5, 33, 88.5) # User to Landing
draw_arrow(51, 93.5, 67, 88.5) # User to Login

# Interfaces to FastAPI
draw_arrow(50, 83.5, 50, 75.5) # Dashboard to API
draw_arrow(33, 83.5, 47, 75.5) # Landing to API
draw_arrow(68, 83.5, 53, 75.5) # Login to API

# FastAPI internal
draw_arrow(50, 70.5, 50, 65.5) # router to orchestrator
draw_arrow(41, 73, 39, 73)     # API <> Auth
draw_arrow(59, 73, 61, 73)     # API <> Background Cache

# Background Task to APIs & DB
draw_arrow(70, 70.5, 23, 52)   # Task to DB (indirect line)
draw_arrow(70, 70.5, 25, 30.5) # Task to USGS

# Orchestrator to DB
draw_arrow(41, 63, 22, 53)

# Orchestrator to External APIs
draw_arrow(45, 60.5, 24, 30.5) # To USGS
draw_arrow(50, 60.5, 49, 30.5) # To OSM/OSRM
draw_arrow(45, 60.5, 24, 20.5) # To GDELT
draw_arrow(50, 60.5, 49, 20.5) # To Nominatim

# Orchestrator to ML Models 
draw_arrow(59, 63, 71, 58) # to Scoring
draw_arrow(59, 63, 71, 48) # to Severity
draw_arrow(59, 63, 71, 38) # to Resource
draw_arrow(59, 63, 71, 28) # to NLP
draw_arrow(59, 63, 71, 18) # to Anomaly

# DB to Orchestrator (Data fetching)
# Already linked above (bi-directional implied or we just need one flow line)

# Clean up axes
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Save higher detail diagram
plt.savefig('pdrdss_detailed_block_diagram.jpg', format='jpg', dpi=300, bbox_inches='tight', pad_inches=0.1)
print("Detailed Diagram saved successfully.")
