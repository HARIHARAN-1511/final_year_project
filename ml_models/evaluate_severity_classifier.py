"""
Evaluate the trained Earthquake Severity Classifier
=====================================================
Reproduces the exact same train/test split (seed=42) used during training,
loads the saved model, and reports all evaluation metrics.
"""

import os
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# ── Reproduce the same synthetic dataset (must match train script exactly) ──
np.random.seed(42)

data_rows = []
labels = []

# CATASTROPHIC
for _ in range(300):
    mag = np.random.uniform(7.0, 9.2)
    depth = np.random.uniform(2, 100)
    tsunami = np.random.choice([0, 1], p=[0.3, 0.7])
    data_rows.append([mag, depth, tsunami])
    labels.append("CATASTROPHIC")

# SEVERE
for _ in range(400):
    mag = np.random.uniform(6.0, 7.5)
    depth = np.random.uniform(5, 300)
    tsunami = np.random.choice([0, 1], p=[0.75, 0.25])
    data_rows.append([mag, depth, tsunami])
    labels.append("SEVERE")

# MODERATE
for _ in range(600):
    mag = np.random.uniform(4.5, 6.2)
    depth = np.random.uniform(5, 400)
    tsunami = 0
    data_rows.append([mag, depth, tsunami])
    labels.append("MODERATE")

# MINOR
for _ in range(700):
    mag = np.random.uniform(2.5, 4.8)
    depth = np.random.uniform(5, 700)
    tsunami = 0
    data_rows.append([mag, depth, tsunami])
    labels.append("MINOR")

X = np.array(data_rows)
y = np.array(labels)

# Same split as training
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Load the trained model ──
model_path = os.path.join(os.path.dirname(__file__), "severity_model.pkl")
model = joblib.load(model_path)
print(f"Loaded model from: {model_path}\n")

# ── Predict on test set ──
y_pred = model.predict(X_test)

# ── Class ordering ──
class_labels = ["MINOR", "MODERATE", "SEVERE", "CATASTROPHIC"]

# ── Metrics ──
acc = accuracy_score(y_test, y_pred)
prec_macro = precision_score(y_test, y_pred, average="macro")
rec_macro = recall_score(y_test, y_pred, average="macro")
f1_macro = f1_score(y_test, y_pred, average="macro")

print("=" * 60)
print("  EARTHQUAKE SEVERITY CLASSIFIER — EVALUATION RESULTS")
print("=" * 60)
print(f"\n  Test samples : {len(y_test)}")
print(f"  Train samples: {len(y_train)}")
print(f"\n  Overall Accuracy  : {acc * 100:.2f}%")
print(f"  Macro Precision   : {prec_macro * 100:.2f}%")
print(f"  Macro Recall      : {rec_macro * 100:.2f}%")
print(f"  Macro F1-Score    : {f1_macro * 100:.2f}%")

print("\n" + "-" * 60)
print("  PER-CLASS CLASSIFICATION REPORT")
print("-" * 60)
print(classification_report(y_test, y_pred, target_names=class_labels, digits=4))

print("-" * 60)
print("  CONFUSION MATRIX")
print("-" * 60)
cm = confusion_matrix(y_test, y_pred, labels=class_labels)

# Pretty-print
header = "Predicted →   " + "  ".join(f"{l:>12}" for l in class_labels)
print(f"\n  {header}")
print("  " + "─" * len(header))
for i, label in enumerate(class_labels):
    row_str = "  ".join(f"{v:>12}" for v in cm[i])
    print(f"  {label:>12} │ {row_str}")

print("\n  (Rows = Actual, Columns = Predicted)")

# ── Per-class precision, recall, f1 ──
prec_per = precision_score(y_test, y_pred, average=None, labels=class_labels)
rec_per = recall_score(y_test, y_pred, average=None, labels=class_labels)
f1_per = f1_score(y_test, y_pred, average=None, labels=class_labels)

print("\n" + "-" * 60)
print("  PER-CLASS SUMMARY TABLE")
print("-" * 60)
print(f"  {'Class':<15} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print(f"  {'─'*15} {'─'*10} {'─'*10} {'─'*10}")
for i, label in enumerate(class_labels):
    print(f"  {label:<15} {prec_per[i]*100:>9.2f}% {rec_per[i]*100:>9.2f}% {f1_per[i]*100:>9.2f}%")

print(f"\n  {'MACRO AVG':<15} {prec_macro*100:>9.2f}% {rec_macro*100:>9.2f}% {f1_macro*100:>9.2f}%")
print("=" * 60)
