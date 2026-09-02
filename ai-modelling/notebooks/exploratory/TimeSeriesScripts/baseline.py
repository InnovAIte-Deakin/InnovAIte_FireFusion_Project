"""
FireFusion — Phase 6: Baseline Models
======================================
Trains and evaluates three baseline models:
1. Persistence baseline (majority class / median)
2. Logistic Regression + Linear Regression (flattened features)
3. Random Forest Classifier + Regressor

All models evaluated on the test set.
Results saved for comparison in Phase 8 benchmarking.

Outputs:
    outputs/06_baseline/baseline_results.json
    outputs/06_baseline/01_confusion_matrix.png/.html
    outputs/06_baseline/02_regression_scatter.png/.html
    outputs/06_baseline/03_feature_importance.png/.html
"""

import os
import json
import time
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                              mean_absolute_error, mean_squared_error, r2_score)
from sklearn.preprocessing import LabelEncoder
warnings.filterwarnings("ignore")

SPLIT_DIR  = "data/splits"
OUTPUT_DIR = "outputs/06_baseline"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PALETTE = {0:"#74C476", 1:"#FDB913", 2:"#F97F08", 3:"#D62728"}

# ── Load splits ────────────────────────────────────────────────────────────
print("Loading splits...")
X_static_train   = np.load(f"{SPLIT_DIR}/X_static_train.npy")
X_temporal_train = np.load(f"{SPLIT_DIR}/X_temporal_train.npy")
y_sev_train      = np.load(f"{SPLIT_DIR}/y_severity_train.npy")
y_area_train     = np.load(f"{SPLIT_DIR}/y_area_train.npy")
y_ros_train      = np.load(f"{SPLIT_DIR}/y_ros_train.npy")

X_static_test    = np.load(f"{SPLIT_DIR}/X_static_test.npy")
X_temporal_test  = np.load(f"{SPLIT_DIR}/X_temporal_test.npy")
y_sev_test       = np.load(f"{SPLIT_DIR}/y_severity_test.npy")
y_area_test      = np.load(f"{SPLIT_DIR}/y_area_test.npy")
y_ros_test       = np.load(f"{SPLIT_DIR}/y_ros_test.npy")

# Flatten temporal for baseline models: (N, 8, 11) -> (N, 88)
X_train_flat = np.hstack([X_static_train,
                           X_temporal_train.reshape(len(X_temporal_train), -1)])
X_test_flat  = np.hstack([X_static_test,
                           X_temporal_test.reshape(len(X_temporal_test), -1)])

print(f"  Train flat: {X_train_flat.shape}")
print(f"  Test flat:  {X_test_flat.shape}")
print(f"  Classes: {np.unique(y_sev_train)}")

results = {}

# ── Helper functions ───────────────────────────────────────────────────────
def clf_metrics(y_true, y_pred, name, t):
    acc = accuracy_score(y_true, y_pred)
    f1  = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    print(f"  {name}: Accuracy={acc:.4f}  F1={f1:.4f}  Time={t:.3f}s")
    return {"accuracy": round(acc,4), "f1_weighted": round(f1,4), "inference_time_s": round(t,4)}

def reg_metrics(y_true, y_pred, name, t):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    print(f"  {name}: MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}  Time={t:.4f}s")
    return {"mae": round(mae,4), "rmse": round(rmse,4), "r2": round(r2,4),
            "inference_time_s": round(t,4)}

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 1 — Persistence Baseline
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 1: Persistence Baseline ────────────────────")
majority_class = int(np.bincount(y_sev_train).argmax())
median_area    = float(np.median(y_area_train))
median_ros     = float(np.median(y_ros_train))

y_persist_sev  = np.full(len(y_sev_test), majority_class)
y_persist_area = np.full(len(y_area_test), median_area)
y_persist_ros  = np.full(len(y_ros_test),  median_ros)

t0 = time.time(); t_inf = time.time() - t0
results["persistence"] = {
    "severity":         clf_metrics(y_sev_test, y_persist_sev, "Persistence (severity)", t_inf),
    "area_ha_log":      reg_metrics(y_area_test, y_persist_area, "Persistence (area)", t_inf),
    "rate_of_spread":   reg_metrics(y_ros_test,  y_persist_ros,  "Persistence (RoS)", t_inf),
}

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 2 — Logistic / Ridge Regression
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 2: Logistic & Ridge Regression ─────────────")

lr_clf = LogisticRegression(max_iter=1000, random_state=42)
t0 = time.time()
lr_clf.fit(X_train_flat, y_sev_train)
t_train = time.time() - t0
t0 = time.time()
y_lr_sev = lr_clf.predict(X_test_flat)
t_inf = time.time() - t0

ridge_area = Ridge(alpha=1.0)
ridge_area.fit(X_train_flat, y_area_train)
y_lr_area = ridge_area.predict(X_test_flat)

ridge_ros = Ridge(alpha=1.0)
ridge_ros.fit(X_train_flat, y_ros_train)
y_lr_ros = ridge_ros.predict(X_test_flat)

results["logistic_ridge"] = {
    "severity":       clf_metrics(y_sev_test, y_lr_sev, "Logistic Regression", t_inf),
    "area_ha_log":    reg_metrics(y_area_test, y_lr_area, "Ridge (area)", time.time()-t0),
    "rate_of_spread": reg_metrics(y_ros_test,  y_lr_ros,  "Ridge (RoS)", time.time()-t0),
    "train_time_s":   round(t_train, 4)
}

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 3 — Random Forest
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Model 3: Random Forest ────────────────────────────")

rf_clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
t0 = time.time()
rf_clf.fit(X_train_flat, y_sev_train)
t_train_rf = time.time() - t0
t0 = time.time()
y_rf_sev = rf_clf.predict(X_test_flat)
t_inf_rf = time.time() - t0

rf_area = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_area.fit(X_train_flat, y_area_train)
y_rf_area = rf_area.predict(X_test_flat)

rf_ros = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_ros.fit(X_train_flat, y_ros_train)
y_rf_ros = rf_ros.predict(X_test_flat)

results["random_forest"] = {
    "severity":       clf_metrics(y_sev_test, y_rf_sev, "Random Forest (severity)", t_inf_rf),
    "area_ha_log":    reg_metrics(y_area_test, y_rf_area, "RF (area)", time.time()-t0),
    "rate_of_spread": reg_metrics(y_ros_test,  y_rf_ros,  "RF (RoS)", time.time()-t0),
    "train_time_s":   round(t_train_rf, 4)
}

# Save results
with open(f"{OUTPUT_DIR}/baseline_results.json","w") as f:
    json.dump(results, f, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — Confusion matrices
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating Chart 1 — Confusion matrices...")

class_labels = [f"C{i+2}" for i in range(len(np.unique(y_sev_test)))]
preds = {
    "Persistence": y_persist_sev,
    "Logistic Regression": y_lr_sev,
    "Random Forest": y_rf_sev
}

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("FireFusion — Confusion Matrices (Severity Classification)",
             fontsize=13, fontweight="bold")
for i, (name, pred) in enumerate(preds.items()):
    cm = confusion_matrix(y_sev_test, pred)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    im = axes[i].imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    axes[i].set_title(name, fontweight="bold")
    axes[i].set_xlabel("Predicted")
    axes[i].set_ylabel("Actual")
    axes[i].set_xticks(range(len(class_labels)))
    axes[i].set_yticks(range(len(class_labels)))
    axes[i].set_xticklabels(class_labels)
    axes[i].set_yticklabels(class_labels)
    for r in range(len(class_labels)):
        for c in range(len(class_labels)):
            axes[i].text(c, r, f"{cm_norm[r,c]:.2f}",
                         ha="center", va="center",
                         color="white" if cm_norm[r,c] > 0.5 else "black",
                         fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.close()

fig_cm = make_subplots(rows=1, cols=3, subplot_titles=list(preds.keys()))
for i, (name, pred) in enumerate(preds.items()):
    cm = confusion_matrix(y_sev_test, pred).astype(float)
    cm_norm = cm / cm.sum(axis=1, keepdims=True)
    fig_cm.add_trace(go.Heatmap(z=cm_norm, x=class_labels, y=class_labels,
        colorscale="Blues", zmin=0, zmax=1, showscale=(i==2),
        text=[[f"{v:.2f}" for v in row] for row in cm_norm],
        texttemplate="%{text}", name=name), row=1, col=i+1)
fig_cm.update_layout(title="Confusion Matrices (Severity)", height=450,
    template="plotly_white")
fig_cm.write_html(f"{OUTPUT_DIR}/01_confusion_matrix.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Regression scatter (area)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 2 — Regression scatter...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("FireFusion — Regression Predictions vs Ground Truth",
             fontsize=13, fontweight="bold")

reg_models = {
    "Persistence": (y_persist_area, y_persist_ros),
    "Ridge":       (y_lr_area, y_lr_ros),
    "Random Forest": (y_rf_area, y_rf_ros)
}
for i, (name, (pred_area, pred_ros)) in enumerate(reg_models.items()):
    # Area
    axes[0][i].scatter(y_area_test, pred_area, alpha=0.3, s=8, color="#1F77B4")
    lo = min(y_area_test.min(), pred_area.min())
    hi = max(y_area_test.max(), pred_area.max())
    axes[0][i].plot([lo,hi],[lo,hi], "r--", alpha=0.8)
    axes[0][i].set_title(f"{name} — Area (log)", fontweight="bold", fontsize=10)
    axes[0][i].set_xlabel("Actual")
    axes[0][i].set_ylabel("Predicted")
    r2 = r2_score(y_area_test, pred_area)
    axes[0][i].text(0.05, 0.92, f"R²={r2:.3f}", transform=axes[0][i].transAxes,
                    fontsize=10, color="navy")
    axes[0][i].grid(alpha=0.3)

    # RoS
    axes[1][i].scatter(y_ros_test, pred_ros, alpha=0.3, s=8, color="#FF7F0E")
    lo = min(y_ros_test.min(), pred_ros.min())
    hi = max(y_ros_test.max(), pred_ros.max())
    axes[1][i].plot([lo,hi],[lo,hi], "r--", alpha=0.8)
    axes[1][i].set_title(f"{name} — Rate of Spread", fontweight="bold", fontsize=10)
    axes[1][i].set_xlabel("Actual")
    axes[1][i].set_ylabel("Predicted")
    r2 = r2_score(y_ros_test, pred_ros)
    axes[1][i].text(0.05, 0.92, f"R²={r2:.3f}", transform=axes[1][i].transAxes,
                    fontsize=10, color="navy")
    axes[1][i].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_regression_scatter.png", dpi=150, bbox_inches="tight")
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# CHART 3 — Random Forest feature importance
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 3 — Feature importance...")

with open("data/scaler_info.json") as f:
    scaler_info = json.load(f)

static_names   = scaler_info["static_cols"]
temporal_names = scaler_info["temporal_cols"]
temporal_steps = [f"{t}_t{s}" for s in range(8) for t in temporal_names]
all_feat_names = static_names + temporal_steps

importances = rf_clf.feature_importances_
# Aggregate temporal features by name (sum across timesteps)
agg_imp = {}
for name in static_names:
    idx = all_feat_names.index(name)
    agg_imp[name] = importances[idx]
for t_name in temporal_names:
    agg_imp[t_name] = sum(
        importances[i] for i, n in enumerate(all_feat_names)
        if n.startswith(t_name + "_t")
    )

imp_series = pd.Series(agg_imp).sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 9))
colors = ["#1F77B4" if n in static_names else "#FF7F0E"
          for n in imp_series.index]
ax.barh(imp_series.index, imp_series.values, color=colors, edgecolor="white")
ax.set_title("Random Forest — Feature Importance (Severity Classification)",
             fontsize=12, fontweight="bold")
ax.set_xlabel("Aggregated Importance")
ax.grid(axis="x", alpha=0.3)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#1F77B4", label="Static"),
                   Patch(color="#FF7F0E", label="Temporal")],
          loc="lower right")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/03_feature_importance.png", dpi=150, bbox_inches="tight")
plt.close()

fig_imp = go.Figure(go.Bar(
    x=imp_series.values, y=imp_series.index, orientation="h",
    marker_color=["#1F77B4" if n in static_names else "#FF7F0E"
                  for n in imp_series.index]
))
fig_imp.update_layout(title="RF Feature Importance (Severity)",
    xaxis_title="Importance", height=600, template="plotly_white")
fig_imp.write_html(f"{OUTPUT_DIR}/03_feature_importance.html")

print(f"\nPhase 6 complete.")
print(f"Saved results → {OUTPUT_DIR}/baseline_results.json")
print(f"Saved charts  → {OUTPUT_DIR}/")