"""
Model 1: Earthquake Severity Classifier
========================================
Trains a RandomForestClassifier to predict disaster severity
based on: magnitude, depth_km, and tsunami flag.

Run once to generate severity_model.pkl:
    python ml_models/train_severity_classifier.py
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ---------------------------------------------------------------------------
# Generate Synthetic Training Data (based on USGS magnitude-depth patterns)
# ---------------------------------------------------------------------------
# Features: [magnitude, depth_km, tsunami_flag]
# Labels:   CATASTROPHIC, SEVERE, MODERATE, MINOR

np.random.seed(42)
N = 2000

data_rows = []
labels = []

# CATASTROPHIC: mag >= 7.0, shallow or with tsunami
for _ in range(300):
    mag = np.random.uniform(7.0, 9.2)
    depth = np.random.uniform(2, 100)
    tsunami = np.random.choice([0, 1], p=[0.3, 0.7])
    data_rows.append([mag, depth, tsunami])
    labels.append("CATASTROPHIC")

# SEVERE: mag 6.0–7.0, or 7.0+ but deep
for _ in range(400):
    mag = np.random.uniform(6.0, 7.5)
    depth = np.random.uniform(5, 300)
    tsunami = np.random.choice([0, 1], p=[0.75, 0.25])
    data_rows.append([mag, depth, tsunami])
    labels.append("SEVERE")

# MODERATE: mag 4.5–6.0
for _ in range(600):
    mag = np.random.uniform(4.5, 6.2)
    depth = np.random.uniform(5, 400)
    tsunami = 0
    data_rows.append([mag, depth, tsunami])
    labels.append("MODERATE")

# MINOR: mag 2.5–4.5
for _ in range(700):
    mag = np.random.uniform(2.5, 4.8)
    depth = np.random.uniform(5, 700)
    tsunami = 0
    data_rows.append([mag, depth, tsunami])
    labels.append("MINOR")

X = np.array(data_rows)
y = np.array(labels)

# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=8,
    random_state=42,
    class_weight="balanced"
)
model.fit(X_train, y_train)

print("=== Severity Classifier Training Report ===")
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
save_path = os.path.join(os.path.dirname(__file__), "severity_model.pkl")
joblib.dump(model, save_path)
print(f"Model saved to: {save_path}")
