"""
Model 3: Resource Demand Forecaster
=====================================
Trains a GradientBoostingRegressor per resource type to predict
how many units of each resource are needed based on:
    - severity_code (0=NONE, 1=MINOR, 2=MODERATE, 3=SEVERE, 4=CATASTROPHIC)
    - population (estimated exposed population)
    - disaster_type_code (0=earthquake, 1=cyclone)

Run once to generate resource_model.pkl:
    python ml_models/train_resource_forecaster.py
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Resource definitions (must match config.py RESOURCE_TYPES order)
# ---------------------------------------------------------------------------
RESOURCE_NAMES = [
    "Water Purification Units",
    "Emergency Shelter Kits",
    "Medical Supply Crates",
    "SAR Equipment Sets",
    "Communication Radios",
    "Portable Generators",
    "Food Ration Packages",
    "Thermal Blankets",
    "First Aid Stations",
    "Evacuation Vehicles",
]

SEVERITY_MAP = {"NONE": 0, "MINOR": 1, "MODERATE": 2, "SEVERE": 3, "CATASTROPHIC": 4}

# ---------------------------------------------------------------------------
# WHO/Sphere Standards baseline multipliers per severity per 1000 people
# ---------------------------------------------------------------------------
# Format: [water, shelter, medical, sar, comms, generators, food, blankets, first_aid, vehicles]
BASELINE_PER_1000 = {
    0: [0,    0,    0,    0,   0,   0,    0,    0,   0,   0],     # NONE
    1: [0.5,  0.5,  0.3,  0.2, 0.2, 0.1,  0.5,  0.5, 0.1, 0.1],  # MINOR
    2: [2,    2,    1,    1,   1,   0.5,  2,    2,   0.5, 0.5],    # MODERATE
    3: [5,    5,    3,    3,   2,   2,    5,    5,   1,   1],      # SEVERE
    4: [10,   10,   7,    7,   5,   5,    10,   10,  3,   3],      # CATASTROPHIC
}

# ---------------------------------------------------------------------------
# Generate Synthetic Training Data
# ---------------------------------------------------------------------------
np.random.seed(42)
N = 3000
X_all = []
y_all = []  # shape: (N, 10) — one target per resource

for _ in range(N):
    sev_code = np.random.randint(0, 5)       # 0-4
    pop = np.random.randint(0, 5_000_000)    # 0–5M
    dis_type = np.random.randint(0, 2)       # 0=earthquake, 1=cyclone

    X_all.append([sev_code, pop, dis_type])

    pop_thous = pop / 1000
    baseline = np.array(BASELINE_PER_1000[sev_code]) * pop_thous

    # Add realistic noise + cyclone modifier (more water/shelter needed)
    noise = np.random.normal(1.0, 0.1, size=len(RESOURCE_NAMES))
    cyclone_mod = np.array([1.3, 1.4, 1.0, 0.8, 1.2, 1.5, 1.3, 1.5, 1.0, 1.2]) if dis_type == 1 else np.ones(len(RESOURCE_NAMES))

    quantities = np.maximum(0, baseline * noise * cyclone_mod).astype(int)
    y_all.append(quantities)

X = np.array(X_all)
y = np.array(y_all)

# ---------------------------------------------------------------------------
# Train one model per resource type
# ---------------------------------------------------------------------------
models = {}
for i, name in enumerate(RESOURCE_NAMES):
    X_train, X_test, y_train, y_test = train_test_split(X, y[:, i], test_size=0.2, random_state=42)
    reg = GradientBoostingRegressor(n_estimators=80, max_depth=4, random_state=42)
    reg.fit(X_train, y_train)
    score = reg.score(X_test, y_test)
    print(f"  {name}: R² = {score:.3f}")
    models[name] = reg

# ---------------------------------------------------------------------------
# Save all models in one file
# ---------------------------------------------------------------------------
save_path = os.path.join(os.path.dirname(__file__), "resource_model.pkl")
joblib.dump({"models": models, "resource_names": RESOURCE_NAMES, "severity_map": SEVERITY_MAP}, save_path)
print(f"\nAll resource models saved to: {save_path}")
