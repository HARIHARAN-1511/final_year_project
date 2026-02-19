"""
Cyclone Severity Classifier
============================
Trains a RandomForestClassifier to predict cyclone severity
based on: wind speed (knots), central pressure (hPa), and storm category code.

Features mirror the Saffir-Simpson Hurricane Wind Scale but add pressure
as an independent predictor — stronger storms have lower pressure.

Run once to generate cyclone_severity_model.pkl:
    python ml_models/train_cyclone_severity_classifier.py
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ---------------------------------------------------------------------------
# Generate Synthetic Training Data
# ---------------------------------------------------------------------------
# Features: [wind_speed_kt, pressure_hpa, intensification_rate_kt_per_6h]
# Labels:   CATASTROPHIC, SEVERE, MODERATE, MINOR, NONE
# Saffir-Simpson proxy + JTWC / IBTrACS wind/pressure patterns

np.random.seed(42)

data_rows = []
labels = []

def pressure_from_wind(wind_kt, noise=True):
    """Approximate empirical relationship: higher wind → lower pressure"""
    base = 1010 - (wind_kt * 1.0)
    if noise:
        base += np.random.normal(0, 15)
    return max(880, min(1015, base))

# CATASTROPHIC: Cat 4/5 equivalent — wind >= 115 kt, pressure < 940 hPa
for _ in range(350):
    wind = np.random.uniform(115, 185)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(5, 30)   # rapid intensification
    data_rows.append([wind, pressure, intensf])
    labels.append("CATASTROPHIC")

# SEVERE: Cat 3 equivalent — wind 65–115 kt, pressure 940–970 hPa
for _ in range(400):
    wind = np.random.uniform(65, 120)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(-5, 20)
    data_rows.append([wind, pressure, intensf])
    labels.append("SEVERE")

# MODERATE: Tropical Storm — wind 34–65 kt, pressure 970–1000 hPa
for _ in range(500):
    wind = np.random.uniform(34, 70)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(-10, 10)
    data_rows.append([wind, pressure, intensf])
    labels.append("MODERATE")

# MINOR: Tropical Depression — wind 15–34 kt
for _ in range(400):
    wind = np.random.uniform(15, 38)
    pressure = pressure_from_wind(wind)
    intensf = np.random.uniform(-15, 5)
    data_rows.append([wind, pressure, intensf])
    labels.append("MINOR")

# NONE: Remnant Low / Extratropical — wind < 15 kt or extratropical
for _ in range(300):
    wind = np.random.uniform(0, 20)
    pressure = np.random.uniform(990, 1020)
    intensf = np.random.uniform(-20, 0)
    data_rows.append([wind, pressure, intensf])
    labels.append("NONE")

X = np.array(data_rows)
y = np.array(labels)

# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=120,
    max_depth=8,
    random_state=42,
    class_weight="balanced"
)
model.fit(X_train, y_train)

print("=== Cyclone Severity Classifier Training Report ===")
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Feature importances
for name, imp in zip(["wind_kt", "pressure_hpa", "intensif_rate"], model.feature_importances_):
    print(f"  Feature importance: {name} = {imp:.3f}")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
save_path = os.path.join(os.path.dirname(__file__), "cyclone_severity_model.pkl")
joblib.dump(model, save_path)
print(f"\nCyclone model saved to: {save_path}")
