import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(22, 18))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

def draw_class_box(ax, x, y, w, name, attributes, methods):
    line_h = 1.6
    pad = 0.6
    font_attr = 10
    font_name = 13

    h_name = line_h + 2 * pad
    h_attr = max(len(attributes), 1) * line_h + 2 * pad
    h_meth = max(len(methods), 1) * line_h + 2 * pad
    total_h = h_name + h_attr + h_meth

    rect = patches.Rectangle((x, y - total_h), w, total_h,
                              linewidth=2, edgecolor='black', facecolor='white', zorder=2)
    ax.add_patch(rect)

    y_name = y - h_name
    ax.plot([x, x + w], [y_name, y_name], color='black', linewidth=2, zorder=3)
    ax.text(x + w / 2, y - h_name / 2, name, ha='center', va='center',
            fontsize=font_name, weight='bold', zorder=4)

    y_attr_end = y_name - h_attr
    ax.plot([x, x + w], [y_attr_end, y_attr_end], color='black', linewidth=2, zorder=3)
    for i, attr in enumerate(attributes):
        ax.text(x + pad, y_name - pad - i * line_h - line_h / 2, attr,
                ha='left', va='center', fontsize=font_attr, family='monospace', zorder=4)

    y_meth_start = y_attr_end
    for i, meth in enumerate(methods):
        ax.text(x + pad, y_meth_start - pad - i * line_h - line_h / 2, meth,
                ha='left', va='center', fontsize=font_attr, family='monospace', weight='bold', zorder=4)

    return total_h


def draw_line(ax, x1, y1, x2, y2, label1="", label2=""):
    ax.plot([x1, x2], [y1, y2], color='black', linewidth=2, zorder=1)
    if label1:
        dx, dy = x2 - x1, y2 - y1
        ax.text(x1 + dx * 0.08, y1 + dy * 0.08 + 0.5, label1,
                ha='center', va='bottom', fontsize=11, weight='bold', zorder=5)
    if label2:
        dx, dy = x2 - x1, y2 - y1
        ax.text(x2 - dx * 0.08, y2 - dy * 0.08 + 0.5, label2,
                ha='center', va='bottom', fontsize=11, weight='bold', zorder=5)


def draw_dashed(ax, x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', linestyle='dashed',
                                color='black', linewidth=1.5), zorder=1)


# ── TITLE ──
ax.text(50, 97, "UML Class Diagram — PDRDSS", ha='center', va='center',
        fontsize=20, weight='bold')

# ═══════════════════════════════════════════════════════════════
# ROW 1: ORM Models
# ═══════════════════════════════════════════════════════════════

w1 = 20
h_user = draw_class_box(ax, 3, 90, w1, "User", [
    "+id: int",
    "+username: str",
    "+hashed_password: str",
    "+role: str",
    "+created_at: datetime",
], [
    "+login()",
    "+logout()",
])

w2 = 22
h_alog = draw_class_box(ax, 28, 90, w2, "AnalysisLog", [
    "+id: int",
    "+location_name: str",
    "+disaster_type: str",
    "+priority_score: float",
    "+severity: str",
    "+timestamp: datetime",
    "+user_id: int  [FK]",
], [
    "+save_report()",
    "+get_history()",
])

w3 = 20
h_dc = draw_class_box(ax, 55, 90, w3, "DisasterCache", [
    "+id: int",
    "+source_id: str",
    "+type: str",
    "+lat: float",
    "+lon: float",
    "+data_json: JSON",
    "+timestamp: datetime",
], [
    "+fetch_data()",
    "+update()",
])

w4 = 18
h_rc = draw_class_box(ax, 80, 90, w4, "ResourceCache", [
    "+id: int",
    "+lat: float",
    "+lon: float",
    "+radius_m: int",
    "+data_json: JSON",
    "+timestamp: datetime",
], [
    "+calculate()",
    "+refresh()",
])

# ═══════════════════════════════════════════════════════════════
# ROW 2: Core Service Classes
# ═══════════════════════════════════════════════════════════════

w5 = 25
h_so = draw_class_box(ax, 5, 48, w5, "ServiceOrchestrator", [
    "-http_client: AsyncClient",
    "-db_session: AsyncSession",
], [
    "+analyze_disaster_impact()",
    "+geocode_location()",
    "+fetch_earthquakes()",
    "+fetch_cyclones()",
    "+fetch_news()",
    "+fetch_resources()",
    "+get_ai_analysis()",
])

w6 = 22
h_se = draw_class_box(ax, 38, 48, w6, "ScoringEngine", [
    "-severity_model: RandomForest",
    "-cyclone_model: RandomForest",
], [
    "+predict_severity()",
    "+predict_cyclone_severity()",
    "+calculate_priority_score()",
    "+calculate_news_urgency()",
])

w7 = 22
h_auth = draw_class_box(ax, 68, 48, w7, "AuthService", [
    "-pwd_context: CryptContext",
    "-secret_key: str",
    "-algorithm: str",
], [
    "+verify_password()",
    "+create_access_token()",
    "+authenticate_user()",
    "+get_current_user()",
])

# ═══════════════════════════════════════════════════════════════
# RELATIONSHIPS
# ═══════════════════════════════════════════════════════════════

# User 1───0..* AnalysisLog
draw_line(ax, 3 + w1, 90 - h_user / 2,
          28, 90 - h_alog / 2,
          label1="1", label2="0..*")

# ServiceOrchestrator ──> AnalysisLog (creates)
draw_line(ax, 5 + w5 * 0.4, 48,
          28 + w2 / 2, 90 - h_alog)

# ServiceOrchestrator ──> DisasterCache
draw_line(ax, 5 + w5 * 0.8, 48,
          55 + w3 / 2, 90 - h_dc,
          label1="1", label2="0..*")

# ServiceOrchestrator ──> ResourceCache
draw_line(ax, 5 + w5, 48 - 2,
          80 + w4 / 2, 90 - h_rc,
          label1="1", label2="0..*")

# ServiceOrchestrator ──> ScoringEngine (uses)
draw_dashed(ax, 5 + w5, 48 - h_so * 0.35,
            38, 48 - h_se * 0.35)

# ServiceOrchestrator ──> AuthService (uses)
draw_dashed(ax, 5 + w5, 48 - h_so * 0.55,
            68, 48 - h_auth * 0.55)

# AuthService ──> User
draw_line(ax, 68 + w7 / 2, 48,
          3 + w1 / 2, 90 - h_user,
          label1="", label2="1..*")

# ═══════════════════════════════════════════════════════════════
ax.set_xlim(-2, 102)
ax.set_ylim(15, 100)
ax.set_aspect('equal')
ax.axis('off')

plt.savefig('uml_class_diagram.jpg', format='jpg', dpi=200, bbox_inches='tight', pad_inches=0.3)
plt.close()
print("Done")
