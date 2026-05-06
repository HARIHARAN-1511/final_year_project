import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(20, 24))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

def draw_entity(ax, x, y, w, h, text):
    outer = patches.Rectangle((x - w/2, y - h/2), w, h,
                               linewidth=2.5, edgecolor='black', facecolor='white', zorder=2)
    inner = patches.Rectangle((x - w/2 + 0.4, y - h/2 + 0.4), w - 0.8, h - 0.8,
                               linewidth=1, edgecolor='black', facecolor='white', zorder=2)
    ax.add_patch(outer)
    ax.add_patch(inner)
    ax.text(x, y, text, ha='center', va='center', fontsize=13, weight='bold', zorder=3)

def draw_process(ax, x, y, r, number, text):
    circle = patches.Circle((x, y), r, linewidth=2.5, edgecolor='black', facecolor='white', zorder=2)
    ax.add_patch(circle)
    ax.plot([x - r, x + r], [y + r * 0.4, y + r * 0.4], color='black', linewidth=1.5, zorder=3)
    ax.text(x, y + r * 0.65, number, ha='center', va='center', fontsize=12, weight='bold', zorder=3)
    ax.text(x, y - r * 0.15, text, ha='center', va='center', fontsize=11, weight='bold', zorder=3)

def draw_datastore(ax, x, y, w, h, text):
    ax.plot([x - w/2, x + w/2], [y + h/2, y + h/2], color='black', linewidth=2.5, zorder=2)
    ax.plot([x - w/2, x + w/2], [y - h/2, y - h/2], color='black', linewidth=2.5, zorder=2)
    ax.plot([x - w/2, x - w/2], [y + h/2, y - h/2], color='black', linewidth=2.5, zorder=2)
    rect = patches.Rectangle((x - w/2, y - h/2), w, h, linewidth=0, facecolor='white', zorder=1)
    ax.add_patch(rect)
    ax.text(x + 0.5, y, text, ha='center', va='center', fontsize=12, weight='bold', zorder=3)

def draw_flow(ax, x1, y1, x2, y2, label, lx, ly):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', linewidth=2, shrinkA=4, shrinkB=4),
                zorder=1)
    ax.text(lx, ly, label, ha='center', va='center', fontsize=10, style='italic', zorder=5)

# ── TITLE ──
ax.text(25, 58, "Data Flow Diagram (Level 1) — PDRDSS", ha='center', va='center',
        fontsize=20, weight='bold')

# ═══════════════════════════════════════════════════════════════
# ENTITIES
# ═══════════════════════════════════════════════════════════════
draw_entity(ax, 8, 53, 11, 3.5, "User /\nEmergency Responder")
draw_entity(ax, 42, 45, 11, 3.5, "External APIs\n(USGS, NOAA, GDELT)")
draw_entity(ax, 42, 33, 11, 3.5, "xAI Grok\nLLM API")

# ═══════════════════════════════════════════════════════════════
# PROCESSES
# ═══════════════════════════════════════════════════════════════
r = 3.2
draw_process(ax, 25, 53, r, "1.0", "User\nAuthentication")
draw_process(ax, 25, 45, r, "2.0", "Disaster Data\nCollection")
draw_process(ax, 25, 37, r, "3.0", "AI/ML Analysis\n& Scoring")
draw_process(ax, 25, 29, r, "4.0", "Decision Support\nOutput")

# ═══════════════════════════════════════════════════════════════
# DATA STORES
# ═══════════════════════════════════════════════════════════════
draw_datastore(ax, 8, 45, 10, 2.2, "D1  SQLite Database")
draw_datastore(ax, 8, 37, 10, 2.2, "D2  Analysis Logs")
draw_datastore(ax, 8, 29, 10, 2.2, "D3  Disaster Cache")

# ═══════════════════════════════════════════════════════════════
# FLOWS
# ═══════════════════════════════════════════════════════════════

# User → 1.0 Auth
draw_flow(ax, 13.5, 53, 21.8, 53, "Login Credentials", 17.5, 54.2)
# 1.0 → User (token back)
draw_flow(ax, 21.8, 51.5, 13.5, 51.5, "JWT Token", 17.5, 50.5)

# 1.0 Auth → D1 Database
draw_flow(ax, 21.8, 51, 13, 46.2, "Validate User", 15, 49)

# 1.0 → 2.0
draw_flow(ax, 25, 49.8, 25, 48.2, "Authorized Request", 20, 49)

# External APIs → 2.0
draw_flow(ax, 36.5, 45, 28.2, 45, "Earthquake, Cyclone,\nNews Data (JSON)", 32, 46.5)

# 2.0 → D3 Cache
draw_flow(ax, 21.8, 43.5, 13, 30.2, "Cache Raw Data", 14.5, 37)

# 2.0 → 3.0 
draw_flow(ax, 25, 41.8, 25, 40.2, "Raw Event Data", 20, 41)

# 3.0 → D2 Logs
draw_flow(ax, 21.8, 37, 13, 37, "Store Analysis", 17.5, 38)

# 3.0 → 4.0
draw_flow(ax, 25, 33.8, 25, 32.2, "Severity, Priority\nScore, Resources", 20, 33)

# 4.0 → xAI Grok
draw_flow(ax, 28.2, 31, 36.5, 33, "Analysis Context", 33, 31)
draw_flow(ax, 36.5, 32, 28.2, 30, "Situation Report", 33, 30)

# 4.0 → User (final output)
draw_flow(ax, 21.8, 29, 13.5, 52, "Dashboard, Alerts,\nReports, Maps", 10, 41)


# ═══════════════════════════════════════════════════════════════
ax.set_xlim(0, 50)
ax.set_ylim(24, 60)
ax.set_aspect('equal')
ax.axis('off')

plt.savefig('data_flow_diagram.jpg', format='jpg', dpi=200, bbox_inches='tight', pad_inches=0.3)
plt.close()
print("Done")
