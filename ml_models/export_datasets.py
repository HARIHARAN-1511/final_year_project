"""
Export Training Datasets to CSV
================================
Generates the same synthetic datasets used to train the ML models
and saves them as CSV files for documentation/review.
"""

import numpy as np
import csv
import os

np.random.seed(42)

OUTPUT_DIR = os.path.dirname(__file__)

# ===================================================================
# DATASET 1: Earthquake Severity Classifier
# ===================================================================
print("Generating earthquake severity dataset...")

eq_rows = []

# CATASTROPHIC: mag >= 7.0, shallow or with tsunami
for _ in range(300):
    mag = np.random.uniform(7.0, 9.2)
    depth = np.random.uniform(2, 100)
    tsunami = np.random.choice([0, 1], p=[0.3, 0.7])
    eq_rows.append([round(mag, 2), round(depth, 2), tsunami, "CATASTROPHIC"])

# SEVERE: mag 6.0–7.0, or 7.0+ but deep
for _ in range(400):
    mag = np.random.uniform(6.0, 7.5)
    depth = np.random.uniform(5, 300)
    tsunami = np.random.choice([0, 1], p=[0.75, 0.25])
    eq_rows.append([round(mag, 2), round(depth, 2), tsunami, "SEVERE"])

# MODERATE: mag 4.5–6.0
for _ in range(600):
    mag = np.random.uniform(4.5, 6.2)
    depth = np.random.uniform(5, 400)
    tsunami = 0
    eq_rows.append([round(mag, 2), round(depth, 2), tsunami, "MODERATE"])

# MINOR: mag 2.5–4.5
for _ in range(700):
    mag = np.random.uniform(2.5, 4.8)
    depth = np.random.uniform(5, 700)
    tsunami = 0
    eq_rows.append([round(mag, 2), round(depth, 2), tsunami, "MINOR"])

eq_path = os.path.join(OUTPUT_DIR, "earthquake_severity_dataset.csv")
with open(eq_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["magnitude", "depth_km", "tsunami_flag", "severity_label"])
    writer.writerows(eq_rows)
print(f"  Saved {len(eq_rows)} rows to {eq_path}")


# ===================================================================
# DATASET 2: Cyclone Severity Classifier
# ===================================================================
print("Generating cyclone severity dataset...")

np.random.seed(42)

def pressure_from_wind(wind_kt):
    base = 1010 - (wind_kt * 1.0)
    base += np.random.normal(0, 15)
    return round(max(880, min(1015, base)), 2)

cy_rows = []

# CATASTROPHIC: Cat 4/5 — wind >= 115 kt
for _ in range(350):
    wind = np.random.uniform(115, 185)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(5, 30)
    cy_rows.append([round(wind, 2), pressure, round(intensf, 2), "CATASTROPHIC"])

# SEVERE: Cat 3 — wind 65–115 kt
for _ in range(400):
    wind = np.random.uniform(65, 120)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(-5, 20)
    cy_rows.append([round(wind, 2), pressure, round(intensf, 2), "SEVERE"])

# MODERATE: Tropical Storm — wind 34–65 kt
for _ in range(500):
    wind = np.random.uniform(34, 70)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(-10, 10)
    cy_rows.append([round(wind, 2), pressure, round(intensf, 2), "MODERATE"])

# MINOR: Tropical Depression — wind 15–34 kt
for _ in range(400):
    wind = np.random.uniform(15, 38)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(-15, 5)
    cy_rows.append([round(wind, 2), pressure, round(intensf, 2), "MINOR"])

# NONE: Remnant — wind < 15 kt
for _ in range(300):
    wind = np.random.uniform(0, 20)
    pressure = np.random.uniform(990, 1020)
    intensf = np.random.uniform(-20, 0)
    cy_rows.append([round(wind, 2), round(pressure, 2), round(intensf, 2), "NONE"])

cy_path = os.path.join(OUTPUT_DIR, "cyclone_severity_dataset.csv")
with open(cy_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["wind_speed_kt", "pressure_hpa", "intensification_rate_kt_per_6h", "severity_label"])
    writer.writerows(cy_rows)
print(f"  Saved {len(cy_rows)} rows to {cy_path}")


# ===================================================================
# DATASET 3: Resource Demand Forecaster
# ===================================================================
print("Generating resource demand dataset...")

np.random.seed(42)

RESOURCE_NAMES = [
    "Water Purification Units", "Emergency Shelter Kits", "Medical Supply Crates",
    "SAR Equipment Sets", "Communication Radios", "Portable Generators",
    "Food Ration Packages", "Thermal Blankets", "First Aid Stations", "Evacuation Vehicles",
]

BASELINE_PER_1000 = {
    0: [0,    0,    0,    0,   0,   0,    0,    0,   0,   0],
    1: [0.5,  0.5,  0.3,  0.2, 0.2, 0.1,  0.5,  0.5, 0.1, 0.1],
    2: [2,    2,    1,    1,   1,   0.5,  2,    2,   0.5, 0.5],
    3: [5,    5,    3,    3,   2,   2,    5,    5,   1,   1],
    4: [10,   10,   7,    7,   5,   5,    10,   10,  3,   3],
}

SEVERITY_LABELS = {0: "NONE", 1: "MINOR", 2: "MODERATE", 3: "SEVERE", 4: "CATASTROPHIC"}
DISASTER_LABELS = {0: "earthquake", 1: "cyclone"}

res_rows = []

for _ in range(3000):
    sev_code = np.random.randint(0, 5)
    pop = np.random.randint(0, 5_000_000)
    dis_type = np.random.randint(0, 2)

    pop_thous = pop / 1000
    baseline = np.array(BASELINE_PER_1000[sev_code]) * pop_thous
    noise = np.random.normal(1.0, 0.1, size=len(RESOURCE_NAMES))
    cyclone_mod = (
        np.array([1.3, 1.4, 1.0, 0.8, 1.2, 1.5, 1.3, 1.5, 1.0, 1.2])
        if dis_type == 1
        else np.ones(len(RESOURCE_NAMES))
    )
    quantities = np.maximum(0, baseline * noise * cyclone_mod).astype(int)

    row = [
        sev_code,
        SEVERITY_LABELS[sev_code],
        pop,
        dis_type,
        DISASTER_LABELS[dis_type],
    ] + quantities.tolist()
    res_rows.append(row)

res_header = [
    "severity_code", "severity_label", "population", "disaster_type_code", "disaster_type_label",
] + [name.lower().replace(" ", "_") for name in RESOURCE_NAMES]

res_path = os.path.join(OUTPUT_DIR, "resource_demand_dataset.csv")
with open(res_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(res_header)
    writer.writerows(res_rows)
print(f"  Saved {len(res_rows)} rows to {res_path}")

print("\nDone! All datasets exported.")
