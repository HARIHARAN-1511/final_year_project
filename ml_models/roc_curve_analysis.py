"""
ROC Curve Analysis — Earthquake Severity Classifier
=====================================================
Generates per-class ROC curves (One-vs-Rest), prints TPR/FPR tables,
computes AUC scores, and saves the ROC curve plot as a PNG image.
"""

import os
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

# ── Reproduce the exact same dataset ──
np.random.seed(42)

data_rows, labels = [], []

for _ in range(300):
    mag = np.random.uniform(7.0, 9.2)
    depth = np.random.uniform(2, 100)
    tsunami = np.random.choice([0, 1], p=[0.3, 0.7])
    data_rows.append([mag, depth, tsunami]); labels.append("CATASTROPHIC")

for _ in range(400):
    mag = np.random.uniform(6.0, 7.5)
    depth = np.random.uniform(5, 300)
    tsunami = np.random.choice([0, 1], p=[0.75, 0.25])
    data_rows.append([mag, depth, tsunami]); labels.append("SEVERE")

for _ in range(600):
    mag = np.random.uniform(4.5, 6.2)
    depth = np.random.uniform(5, 400)
    data_rows.append([mag, depth, 0]); labels.append("MODERATE")

for _ in range(700):
    mag = np.random.uniform(2.5, 4.8)
    depth = np.random.uniform(5, 700)
    data_rows.append([mag, depth, 0]); labels.append("MINOR")

X = np.array(data_rows)
y = np.array(labels)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Load model ──
model_path = os.path.join(os.path.dirname(__file__), "severity_model.pkl")
model = joblib.load(model_path)

# ── Class labels ──
class_labels = ["MINOR", "MODERATE", "SEVERE", "CATASTROPHIC"]
n_classes = len(class_labels)

# ── Binarize true labels for OvR ROC ──
y_test_bin = label_binarize(y_test, classes=class_labels)

# ── Get probability predictions ──
y_prob = model.predict_proba(X_test)

# Align probability columns with class_labels order
model_classes = list(model.classes_)
prob_aligned = np.zeros((len(y_test), n_classes))
for i, label in enumerate(class_labels):
    idx = model_classes.index(label)
    prob_aligned[:, i] = y_prob[:, idx]

# ── Compute ROC curve and AUC for each class ──
fpr = {}
tpr = {}
roc_auc = {}

print("=" * 65)
print("  ROC CURVE DATA — EARTHQUAKE SEVERITY CLASSIFIER")
print("=" * 65)

for i, label in enumerate(class_labels):
    fpr[label], tpr[label], thresholds = roc_curve(y_test_bin[:, i], prob_aligned[:, i])
    roc_auc[label] = auc(fpr[label], tpr[label])

    print(f"\n{'─' * 65}")
    print(f"  Class: {label}  |  AUC = {roc_auc[label]:.4f}")
    print(f"{'─' * 65}")
    print(f"  {'FPR':>10}  {'TPR':>10}  {'Threshold':>10}")
    print(f"  {'─'*10}  {'─'*10}  {'─'*10}")

    # Print sampled points (every few points to keep output manageable)
    n_points = len(fpr[label])
    if n_points <= 20:
        indices = range(n_points)
    else:
        step = max(1, n_points // 15)
        indices = list(range(0, n_points, step))
        if indices[-1] != n_points - 1:
            indices.append(n_points - 1)

    for j in indices:
        print(f"  {fpr[label][j]:>10.4f}  {tpr[label][j]:>10.4f}  {thresholds[j]:>10.4f}")

# ── Compute Macro-Average ROC ──
all_fpr = np.unique(np.concatenate([fpr[l] for l in class_labels]))
mean_tpr = np.zeros_like(all_fpr)
for label in class_labels:
    mean_tpr += np.interp(all_fpr, fpr[label], tpr[label])
mean_tpr /= n_classes
macro_auc = auc(all_fpr, mean_tpr)

# ── Micro-Average ROC ──
fpr_micro, tpr_micro, _ = roc_curve(y_test_bin.ravel(), prob_aligned.ravel())
micro_auc = auc(fpr_micro, tpr_micro)

print(f"\n{'=' * 65}")
print(f"  AUC SUMMARY")
print(f"{'=' * 65}")
print(f"  {'Class':<15} {'AUC Score':>10}")
print(f"  {'─'*15} {'─'*10}")
for label in class_labels:
    print(f"  {label:<15} {roc_auc[label]:>10.4f}")
print(f"  {'─'*15} {'─'*10}")
print(f"  {'Macro-Avg':<15} {macro_auc:>10.4f}")
print(f"  {'Micro-Avg':<15} {micro_auc:>10.4f}")
print(f"{'=' * 65}")

# ── Plot ROC Curves ──
fig, ax = plt.subplots(1, 1, figsize=(8, 6))

colors = ["#2563eb", "#16a34a", "#ea580c", "#dc2626"]
for i, label in enumerate(class_labels):
    ax.plot(
        fpr[label], tpr[label],
        color=colors[i], lw=2,
        label=f"{label} (AUC = {roc_auc[label]:.3f})"
    )

# Macro average
ax.plot(
    all_fpr, mean_tpr,
    color="black", lw=2, linestyle="--",
    label=f"Macro-Avg (AUC = {macro_auc:.3f})"
)

# Diagonal
ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle=":")

ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])
ax.set_xlabel("False Positive Rate (FPR)", fontsize=12)
ax.set_ylabel("True Positive Rate (TPR)", fontsize=12)
ax.set_title("ROC Curves — Earthquake Severity Classifier\n(One-vs-Rest)", fontsize=13, fontweight="bold")
ax.legend(loc="lower right", fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
save_path = os.path.join(os.path.dirname(__file__), "..", "roc_curve_severity.png")
plt.savefig(save_path, dpi=150)
print(f"\n  ROC curve plot saved to: {os.path.abspath(save_path)}")
