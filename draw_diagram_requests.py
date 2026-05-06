import matplotlib.pyplot as plt
import matplotlib.patches as patches

def setup_plot(title):
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.text(50, 95, title, ha='center', va='center', fontsize=18, weight='bold')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    return fig, ax

def draw_block(ax, x, y, width, height, text, bold=True):
    rect = patches.Rectangle((x - width/2, y - height/2), width, height,
                             linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(rect)
    fw = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=11, color='black', weight=fw)

def draw_actor(ax, x, y, text):
    circle = patches.Circle((x, y+3), 1.8, linewidth=2, edgecolor='black', facecolor='white', zorder=3)
    ax.add_patch(circle)
    ax.plot([x, x], [y+1.2, y-3], color='black', linewidth=2, zorder=3)
    ax.plot([x-2.5, x+2.5], [y, y], color='black', linewidth=2, zorder=3)
    ax.plot([x, x-2.5], [y-3, y-6], color='black', linewidth=2, zorder=3)
    ax.plot([x, x+2.5], [y-3, y-6], color='black', linewidth=2, zorder=3)
    ax.text(x, y-8, text, ha='center', va='top', fontsize=11, color='black', weight='bold')

def draw_oval(ax, x, y, width, height, text):
    oval = patches.Ellipse((x, y), width, height, linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(oval)
    ax.text(x, y, text, ha='center', va='center', fontsize=10, color='black')

def draw_arrow(ax, sx, sy, ex, ey):
    ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                arrowprops=dict(facecolor='black', edgecolor='black', shrink=0.01, width=1.5, headwidth=8, headlength=10))

def draw_line(ax, sx, sy, ex, ey):
    ax.plot([sx, ex], [sy, ey], color='black', linewidth=2)

def generate_use_case():
    fig, ax = setup_plot("UML Use Case Diagram")
    
    # System boundary
    rect = patches.Rectangle((35, 15), 45, 75, linewidth=2, edgecolor='black', facecolor='none', linestyle='-')
    ax.add_patch(rect)
    ax.text(57.5, 87, "PRDSSS", ha='center', va='bottom', fontsize=16, weight='bold')
    
    # Actors
    draw_actor(ax, 15, 70, "User / Admin")
    draw_actor(ax, 15, 30, "Emergency Responder")
    draw_actor(ax, 90, 50, "External Data APIs\n(USGS, NOAA, GDELT)")
    
    # Use cases
    y_starts = [80, 68, 56, 44, 32, 20]
    cases = [
        "Login / Authenticate", 
        "View Interactive Dashboard", 
        "Ingest Sensor / News Data", 
        "Analyze Disaster Severity", 
        "Forecast Resource Needs", 
        "Generate Situation Report"
    ]
    for y, text in zip(y_starts, cases):
        draw_oval(ax, 57.5, y, 32, 8, text)
        
    # User connections
    draw_line(ax, 20, 70, 41.5, 80)
    draw_line(ax, 20, 70, 41.5, 68)
    draw_line(ax, 20, 70, 41.5, 56)
    
    # Responder connections
    draw_line(ax, 20, 30, 41.5, 68)
    draw_line(ax, 20, 30, 41.5, 44)
    draw_line(ax, 20, 30, 41.5, 32)
    draw_line(ax, 20, 30, 41.5, 20)
    
    # External API connections
    draw_line(ax, 85, 50, 73.5, 56)
    draw_line(ax, 85, 50, 73.5, 44)

    plt.savefig('uml_use_case.jpg', format='jpg', dpi=300, bbox_inches='tight')
    plt.close()

def draw_class(ax, x, y, width, name, attributes, methods):
    h_name = 5
    h_attr = len(attributes) * 3 + 2
    h_meth = len(methods) * 3 + 2 if methods else 2
    total_h = h_name + h_attr + h_meth
    
    rect = patches.Rectangle((x - width/2, y - total_h/2), width, total_h, linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(rect)
    
    y_sep1 = y + total_h/2 - h_name
    ax.plot([x - width/2, x + width/2], [y_sep1, y_sep1], color='black', linewidth=2)
    y_sep2 = y_sep1 - h_attr
    ax.plot([x - width/2, x + width/2], [y_sep2, y_sep2], color='black', linewidth=2)
    
    ax.text(x, y + total_h/2 - h_name/2, name, ha='center', va='center', weight='bold', fontsize=12)
    
    curr_y = y_sep1 - 3
    for attr in attributes:
        ax.text(x - width/2 + 2, curr_y, attr, ha='left', va='center', fontsize=10)
        curr_y -= 3
        
    curr_y = y_sep2 - 3
    for meth in methods:
        ax.text(x - width/2 + 2, curr_y, meth, ha='left', va='center', fontsize=10)
        curr_y -= 3
        
    return total_h

def generate_class_diagram():
    fig, ax = setup_plot("UML Class Diagram")
    
    user_attrs = ["+ id: int", "+ username: str", "+ hashed_password: str", "+ role: str", "+ created_at: datetime"]
    analysis_attrs = ["+ id: int", "+ location_name: str", "+ disaster_type: str", "+ priority_score: float", "+ severity: str", "+ timestamp: datetime", "+ user_id: int"]
    disaster_attrs = ["+ id: int", "+ source_id: str", "+ type: str", "+ lat: float", "+ lon: float", "+ data_json: json", "+ timestamp: datetime"]
    resource_attrs = ["+ id: int", "+ lat: float", "+ lon: float", "+ radius_m: int", "+ data_json: json", "+ timestamp: datetime"]
    
    draw_class(ax, 30, 72, 38, "User", user_attrs, ["+ login()", "+ logout()"])
    draw_class(ax, 30, 28, 38, "AnalysisLog", analysis_attrs, ["+ generate_score()", "+ save_report()"])
    
    draw_class(ax, 75, 72, 35, "DisasterCache", disaster_attrs, ["+ fetch_data()", "+ update()"])
    draw_class(ax, 75, 28, 35, "ResourceCache", resource_attrs, ["+ calculate()", "+ refresh()"])
    
    # Draw relation between User and AnalysisLog
    draw_line(ax, 30, 56.5, 30, 48.5)
    ax.text(32, 54, "1", ha='left', va='center', weight='bold')
    ax.text(32, 51, "*", ha='left', va='center', weight='bold')
    
    plt.savefig('uml_class_diagram.jpg', format='jpg', dpi=300, bbox_inches='tight')
    plt.close()

def generate_dfd():
    fig, ax = setup_plot("Data Flow Diagram (Level 0)")
    
    draw_block(ax, 20, 75, 24, 10, "User / Responder")
    draw_block(ax, 80, 75, 24, 10, "External APIs\n(Quakes, Cyclones, News)")
    
    draw_oval(ax, 50, 50, 40, 25, "0\nPRDSSS Service Orchestrator\n(Data Processing & Analytics)")
    
    # Data Store open box
    ax.plot([35, 65], [23, 23], color='black', linewidth=2)
    ax.plot([35, 65], [12, 12], color='black', linewidth=2)
    ax.plot([35, 35], [23, 12], color='black', linewidth=2)
    ax.text(50, 17.5, "D1 SQLite Database / Cache", ha='center', va='center', weight='bold')
    
    # Flows
    draw_arrow(ax, 25, 70, 40, 60)
    ax.text(31, 67, "Auth / Dashboard\nRequests", ha='center', va='center', fontsize=9)
    
    draw_arrow(ax, 45, 62, 30, 72)
    ax.text(40, 73, "Alerts, Visualizations,\nSituation Reports", ha='center', va='center', fontsize=9)
    
    draw_arrow(ax, 60, 62, 75, 72)
    ax.text(67, 69, "Data Pull\nRequests", ha='center', va='center', fontsize=9)
    
    draw_arrow(ax, 72, 70, 58, 58)
    ax.text(78, 62, "Raw JSON\nTelemetries", ha='center', va='center', fontsize=9)
    
    draw_arrow(ax, 45, 37.5, 45, 25) # Orchestrator to DB
    ax.text(35, 32, "Store Logs & Models", ha='center', va='center', fontsize=9)
    
    draw_arrow(ax, 55, 25, 55, 37.5) # DB to Orchestrator
    ax.text(63, 32, "Retrieve Cache", ha='center', va='center', fontsize=9)
    
    plt.savefig('data_flow_diagram.jpg', format='jpg', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    generate_use_case()
    generate_class_diagram()
    generate_dfd()
    print("Done")
