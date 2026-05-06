import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_group(ax, x, y, width, height, text):
    rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                             linewidth=2, linestyle='--', edgecolor='black', facecolor='none')
    ax.add_patch(rect)
    ax.text(x, y + height/2 + 2, text, ha='center', va='bottom', fontsize=14, color='black', weight='bold')

def draw_block(ax, x, y, width, height, text, bold=True):
    rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                             linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(rect)
    fw = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=11, color='black', weight=fw)

def draw_arrow(ax, sx, sy, ex, ey):
    ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(facecolor='black', edgecolor='black', shrink=0.02, width=1.5, headwidth=8, headlength=10))

def generate_aiml_diagram():
    fig, ax = plt.subplots(figsize=(14, 12))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    ax.text(50, 95, "AI & Machine Learning Core Architecture", ha='center', va='center', fontsize=18, weight='bold')
    
    # Blocks
    draw_block(ax, 50, 85, 40, 8, "Service Orchestrator\n(Input Data: Sensor, News, DB)")
    
    # The models
    draw_group(ax, 50, 55, 85, 35, "Predictive Models & Analysis")
    
    draw_block(ax, 20, 65, 23, 8, "Severity Classifier\n(Random Forest ML)")
    draw_block(ax, 50, 65, 23, 8, "Anomaly Detector\n(Isolation Forest)")
    draw_block(ax, 80, 65, 23, 8, "News NLP Engine\n(HuggingFace & Transformers)")
    
    draw_block(ax, 35, 45, 23, 8, "Resource Forecaster\n(Gradient Boosting)")
    draw_block(ax, 65, 45, 23, 8, "Risk Scoring Engine\n(Aggregation & Formula)")
    
    draw_block(ax, 50, 25, 30, 8, "xAI Grok API\n(Decision Support GenAI)")
    
    draw_block(ax, 50, 10, 40, 8, "Service Orchestrator\n(Final Analysis Output Response)")
    
    # Arrows from orchestrator to models
    draw_arrow(ax, 50, 81, 20, 69)
    draw_arrow(ax, 50, 81, 50, 69)
    draw_arrow(ax, 50, 81, 80, 69)
    
    # Arrows from models to next step
    draw_arrow(ax, 20, 61, 35, 49) # severity to forecaster
    draw_arrow(ax, 20, 61, 65, 49) # severity to scoring
    draw_arrow(ax, 50, 61, 65, 49) # anomaly to scoring
    draw_arrow(ax, 80, 61, 65, 49) # nlp to scoring
    
    # arrows from scoring/forecaster to genAI
    draw_arrow(ax, 35, 41, 50, 29)
    draw_arrow(ax, 65, 41, 50, 29)
    
    # to output
    draw_arrow(ax, 50, 21, 50, 14)
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    plt.savefig('aiml_core_diagram.jpg', format='jpg', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()

def generate_orchestrator_diagram():
    fig, ax = plt.subplots(figsize=(14, 12))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    ax.text(50, 95, "Service Orchestrator Architecture", ha='center', va='center', fontsize=18, weight='bold')
    
    # Blocks
    draw_block(ax, 50, 80, 30, 8, "API Router & Authentication\n(FastAPI layer)")
    
    # Core Orchestrator
    draw_group(ax, 50, 50, 35, 25, "Central Hub")
    draw_block(ax, 50, 50, 30, 18, "Service Orchestrator\n(Data Routing, Coordination,\nTransaction Management)")
    
    # Top Left Data
    draw_block(ax, 20, 70, 25, 8, "SQLite Database\n(Users & History)")
    draw_block(ax, 20, 50, 25, 8, "Background Tasks\n(Redis/TTL Cache)")
    
    # External APIs
    draw_group(ax, 80, 60, 30, 45, "External Data APIs")
    draw_block(ax, 80, 75, 25, 6, "USGS (Earthquakes)")
    draw_block(ax, 80, 65, 25, 6, "NOAA (Cyclones)")
    draw_block(ax, 80, 55, 25, 6, "GDELT (News API)")
    draw_block(ax, 80, 45, 25, 6, "OSM / OSRM (Maps)")
    
    # Bottom ML
    draw_block(ax, 50, 20, 35, 8, "AI & ML Core Engine\n(Analysis, Forecast, Grok)")
    
    # Arrows
    # In/Out from Router
    draw_arrow(ax, 50, 76, 50, 59)
    draw_arrow(ax, 48, 59, 48, 76)
    
    # Flow to External
    draw_arrow(ax, 65, 52, 67, 75)
    draw_arrow(ax, 65, 51, 67, 65)
    draw_arrow(ax, 65, 49, 67, 55)
    draw_arrow(ax, 65, 48, 67, 45)
    
    # Flow back from External
    draw_arrow(ax, 67, 74, 65, 54)
    draw_arrow(ax, 67, 64, 65, 53)
    draw_arrow(ax, 67, 54, 65, 50)
    draw_arrow(ax, 67, 44, 65, 47)
    
    # Flow DB/Cache
    draw_arrow(ax, 35, 50, 32, 50)
    draw_arrow(ax, 32, 52, 35, 52)
    
    draw_arrow(ax, 35, 55, 32, 68)
    draw_arrow(ax, 30, 68, 35, 57)
    
    # Flow ML Core
    draw_arrow(ax, 48, 41, 48, 24)
    draw_arrow(ax, 52, 24, 52, 41)
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    plt.savefig('service_orchestrator_diagram.jpg', format='jpg', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()

if __name__ == "__main__":
    generate_aiml_diagram()
    generate_orchestrator_diagram()
    print("Both diagrams generated successfully in JPG format.")
