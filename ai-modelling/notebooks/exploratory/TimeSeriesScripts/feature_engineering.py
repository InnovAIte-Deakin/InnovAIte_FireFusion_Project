"""
FireFusion — Phase 4: Feature Engineering
==========================================
Transforms raw features into model-ready inputs:
- Lag features (lag-1, lag-2) per cell
- Delta features (rate of change between timesteps)
- Rolling statistics (mean, std over 2-step window)
- FFDI proxy composite feature
- Normalisation (min-max for temporal, z-score for static)
- Saves engineered flat + tensor datasets

Outputs:
    data/data_engineered_flat.csv
    data/data_engineered_temporal.csv
    data/X_static.npy       shape (N, 8)
    data/X_temporal.npy     shape (N, 8, features)
    data/y_severity.npy     shape (N,)
    data/y_area.npy         shape (N,)
    data/y_ros.npy          shape (N,)
    outputs/04_features/01_feature_importance_corr.png/.html
    outputs/04_features/02_ffdi_distribution.png/.html
    outputs/04_features/03_normalisation_check.png/.html
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.preprocessing import MinMaxScaler, StandardScaler
warnings.filterwarnings("ignore")

DATA_DIR   = "data"
OUTPUT_DIR = "outputs/04_features"
os.makedirs(OUTPUT_DIR, exist_ok=True)

STATIC_FEATURES   = ["elevation_m","slope_deg","aspect_deg","dist_to_water_m",
                      "veg_type_encoded","ndvi_at_ignition","ndwi_at_ignition","nbr_at_ignition"]
TEMPORAL_FEATURES = ["max_temp_c","wind_speed_kmh","wind_dir_deg","rel_humidity_pct",
                      "precipitation_mm","evapotranspiration","soil_moisture",
                      "soil_temp_c","days_since_rain","years_since_last_fire"]
TARGET_LABELS     = ["severity_class","area_ha_burned","rate_of_spread_ha_per_day"]

print("Loading data...")
df_flat = pd.read_csv(f"{DATA_DIR}/data_flat.csv")
df_temp = pd.read_csv(f"{DATA_DIR}/data_temporal.csv")
df_flat["severity_class"] = df_flat["severity_class"].astype(int)
df_temp["severity_class"] = df_temp["severity_class"].astype(int)
df_temp["timestep_idx"]   = (df_temp["day"] + 3) * 2 + (df_temp["hour"] == 18).astype(int)
print(f"  Flat: {df_flat.shape}   Temporal: {df_temp.shape}")

# ── Per-cell temporal feature engineering ──────────────────────────────────
print("Engineering temporal features per cell...")

df_temp_eng = df_temp.sort_values(["cell_id","timestep_idx"]).copy()

for feat in ["max_temp_c","wind_speed_kmh","rel_humidity_pct",
             "soil_moisture","evapotranspiration"]:
    # Lag-1 and lag-2
    df_temp_eng[f"{feat}_lag1"] = df_temp_eng.groupby("cell_id")[feat].shift(1)
    df_temp_eng[f"{feat}_lag2"] = df_temp_eng.groupby("cell_id")[feat].shift(2)

    # Delta (rate of change)
    df_temp_eng[f"{feat}_delta"] = df_temp_eng.groupby("cell_id")[feat].diff()

    # Rolling mean and std (2-step window)
    df_temp_eng[f"{feat}_roll_mean"] = (
        df_temp_eng.groupby("cell_id")[feat]
        .transform(lambda x: x.rolling(2, min_periods=1).mean())
    )
    df_temp_eng[f"{feat}_roll_std"] = (
        df_temp_eng.groupby("cell_id")[feat]
        .transform(lambda x: x.rolling(2, min_periods=1).std().fillna(0))
    )

# FFDI proxy composite feature per timestep
df_temp_eng["ffdi_proxy"] = (
    df_temp_eng["max_temp_c"]         * 0.80 +
    df_temp_eng["wind_speed_kmh"]     * 0.40 +
    (100 - df_temp_eng["rel_humidity_pct"]) * 0.30 -
    df_temp_eng["soil_moisture"]      * 20.0 +
    df_temp_eng["days_since_rain"]    * 0.20
).clip(0, 120)

print(f"  Engineered temporal shape: {df_temp_eng.shape}")
print(f"  New features added: lag1/lag2/delta/roll_mean/roll_std + ffdi_proxy")

# ── Log-transform area_ha_burned ───────────────────────────────────────────
df_flat["area_ha_log"] = np.log1p(df_flat["area_ha_burned"])

# ── Normalisation ──────────────────────────────────────────────────────────
print("Normalising features...")

# Static — z-score (StandardScaler)
static_scaler = StandardScaler()
df_static_scaled = df_flat[STATIC_FEATURES].copy()
df_static_scaled[STATIC_FEATURES] = static_scaler.fit_transform(
    df_flat[STATIC_FEATURES].fillna(0)
)

# Temporal — min-max [0, 1] (MinMaxScaler)
temporal_base_cols = TEMPORAL_FEATURES + ["ffdi_proxy"]
temporal_scaler = MinMaxScaler()
df_temp_scaled = df_temp_eng.copy()
df_temp_scaled[temporal_base_cols] = temporal_scaler.fit_transform(
    df_temp_eng[temporal_base_cols].fillna(0)
)

# ── Build numpy tensors ────────────────────────────────────────────────────
print("Building numpy tensors...")

# Final temporal feature set for model
TEMPORAL_MODEL_FEATURES = TEMPORAL_FEATURES + ["ffdi_proxy"]

cell_ids = df_flat["cell_id"].values
N = len(cell_ids)
T = 8
F_static   = len(STATIC_FEATURES)
F_temporal = len(TEMPORAL_MODEL_FEATURES)

X_static   = np.zeros((N, F_static),   dtype=np.float32)
X_temporal = np.zeros((N, T, F_temporal), dtype=np.float32)
y_severity = np.zeros(N, dtype=np.int32)
y_area     = np.zeros(N, dtype=np.float32)
y_ros      = np.zeros(N, dtype=np.float32)

temporal_grouped = df_temp_scaled.sort_values(
    ["cell_id","timestep_idx"]).groupby("cell_id")

for i, cid in enumerate(cell_ids):
    # Static
    X_static[i] = df_static_scaled[df_flat["cell_id"] == cid][STATIC_FEATURES].values[0]

    # Temporal
    if cid in temporal_grouped.groups:
        grp = temporal_grouped.get_group(cid).sort_values("timestep_idx")
        vals = grp[TEMPORAL_MODEL_FEATURES].values
        if len(vals) == T:
            X_temporal[i] = vals
        else:
            X_temporal[i, :len(vals)] = vals[:T]

    # Labels
    row = df_flat[df_flat["cell_id"] == cid].iloc[0]
    y_severity[i] = int(row["severity_class"])
    y_area[i]     = float(row["area_ha_log"])
    y_ros[i]      = float(row["rate_of_spread_ha_per_day"])

# Remap severity to 0-indexed for classification
severity_map = {v: i for i, v in enumerate(sorted(np.unique(y_severity)))}
y_severity_mapped = np.array([severity_map[s] for s in y_severity], dtype=np.int32)

print(f"  X_static shape:   {X_static.shape}")
print(f"  X_temporal shape: {X_temporal.shape}")
print(f"  y_severity shape: {y_severity_mapped.shape}  classes: {np.unique(y_severity_mapped)}")
print(f"  y_area shape:     {y_area.shape}")
print(f"  y_ros shape:      {y_ros.shape}")

# Save scalers info
scaler_info = {
    "static_mean":  static_scaler.mean_.tolist(),
    "static_std":   static_scaler.scale_.tolist(),
    "static_cols":  STATIC_FEATURES,
    "temporal_min": temporal_scaler.data_min_.tolist(),
    "temporal_max": temporal_scaler.data_max_.tolist(),
    "temporal_cols": temporal_base_cols,
    "severity_map": {int(k): int(v) for k, v in severity_map.items()},
    "n_classes":    len(severity_map)
}
import json
with open(f"{DATA_DIR}/scaler_info.json","w") as f:
    json.dump(scaler_info, f, indent=2)

# ── Save ───────────────────────────────────────────────────────────────────
np.save(f"{DATA_DIR}/X_static.npy",   X_static)
np.save(f"{DATA_DIR}/X_temporal.npy", X_temporal)
np.save(f"{DATA_DIR}/y_severity.npy", y_severity_mapped)
np.save(f"{DATA_DIR}/y_area.npy",     y_area)
np.save(f"{DATA_DIR}/y_ros.npy",      y_ros)
df_temp_eng.to_csv(f"{DATA_DIR}/data_engineered_temporal.csv", index=False)
df_flat.to_csv(f"{DATA_DIR}/data_engineered_flat.csv", index=False)

# ── Chart 1 — Correlation with severity ───────────────────────────────────
print("Generating Chart 1 — Feature correlation with severity...")

ignition_cols = [f"ignition_{f}" for f in TEMPORAL_FEATURES if f"ignition_{f}" in df_flat.columns]
corr_cols = STATIC_FEATURES + ignition_cols
corr_with_sev = df_flat[corr_cols + ["severity_class"]].corr()["severity_class"].drop("severity_class")
corr_sorted = corr_with_sev.abs().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 10))
colors = ["#D62728" if corr_with_sev[f] < 0 else "#1F77B4" for f in corr_sorted.index]
bars = ax.barh(corr_sorted.index, corr_sorted.values, color=colors, edgecolor="white")
ax.set_title("Feature Correlation with Severity Class (absolute)",
             fontsize=13, fontweight="bold")
ax.set_xlabel("Absolute Pearson Correlation")
ax.axvline(x=0.1, color="gray", linestyle="--", alpha=0.5, label="Threshold 0.1")
ax.grid(axis="x", alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_feature_importance_corr.png", dpi=150, bbox_inches="tight")
plt.close()

fig_corr = go.Figure(go.Bar(
    x=corr_sorted.values, y=corr_sorted.index,
    orientation="h",
    marker_color=["#D62728" if corr_with_sev[f] < 0 else "#1F77B4"
                  for f in corr_sorted.index],
))
fig_corr.update_layout(title="Feature Correlation with Severity Class",
    xaxis_title="Absolute Correlation", height=600, template="plotly_white")
fig_corr.write_html(f"{OUTPUT_DIR}/01_feature_importance_corr.html")

# ── Chart 2 — FFDI proxy distribution ─────────────────────────────────────
print("Generating Chart 2 — FFDI distribution...")

ffdi_ignition = df_temp_eng[
    (df_temp_eng["day"] == 0) & (df_temp_eng["hour"] == 18)
].copy()
if "severity_class" not in ffdi_ignition.columns:
    ffdi_ignition = ffdi_ignition.merge(
        df_flat[["cell_id","severity_class"]], on="cell_id"
    )
ffdi_ignition["severity_class"] = ffdi_ignition["severity_class"].astype(int)

PALETTE = {2:"#74C476", 3:"#FDB913", 4:"#F97F08", 5:"#D62728"}

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("FireFusion — FFDI Proxy Distribution", fontsize=13, fontweight="bold")

for sev in sorted(ffdi_ignition["severity_class"].unique()):
    vals = ffdi_ignition[ffdi_ignition["severity_class"] == sev]["ffdi_proxy"]
    axes[0].hist(vals, bins=40, alpha=0.6, label=f"Class {sev}",
                 color=PALETTE.get(sev,"gray"), density=True)
axes[0].set_title("FFDI Proxy by Severity Class (day 0, 18:00)")
axes[0].set_xlabel("FFDI Proxy Score")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].boxplot(
    [ffdi_ignition[ffdi_ignition["severity_class"] == s]["ffdi_proxy"].dropna()
     for s in sorted(ffdi_ignition["severity_class"].unique())],
    tick_labels=[f"Class {s}" for s in sorted(ffdi_ignition["severity_class"].unique())],
    patch_artist=True,
    boxprops=dict(facecolor="#F97F08"),
    medianprops=dict(color="white", linewidth=2)
)
axes[1].set_title("FFDI Proxy Box Plot by Severity Class")
axes[1].grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_ffdi_distribution.png", dpi=150, bbox_inches="tight")
plt.close()

fig_ffdi = px.box(ffdi_ignition, x="severity_class", y="ffdi_proxy",
    color="severity_class", title="FFDI Proxy by Severity Class",
    color_discrete_map={k: v for k, v in PALETTE.items()})
fig_ffdi.update_layout(template="plotly_white")
fig_ffdi.write_html(f"{OUTPUT_DIR}/02_ffdi_distribution.html")

# ── Chart 3 — Normalisation check ─────────────────────────────────────────
print("Generating Chart 3 — Normalisation check...")

fig, axes = plt.subplots(2, 5, figsize=(20, 8))
fig.suptitle("FireFusion — Temporal Features After Min-Max Normalisation",
             fontsize=13, fontweight="bold")
axes = axes.flatten()
for i, feat in enumerate(TEMPORAL_FEATURES):
    vals = df_temp_scaled[feat].dropna()
    axes[i].hist(vals, bins=40, color="#1F77B4", edgecolor="white", alpha=0.8)
    axes[i].set_title(feat, fontsize=9, fontweight="bold")
    axes[i].set_xlim(-0.1, 1.1)
    axes[i].axvline(x=0, color="red", linestyle="--", alpha=0.4)
    axes[i].axvline(x=1, color="red", linestyle="--", alpha=0.4)
    axes[i].grid(alpha=0.2)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/03_normalisation_check.png", dpi=150, bbox_inches="tight")
plt.close()

fig_norm = make_subplots(rows=2, cols=5, subplot_titles=TEMPORAL_FEATURES)
for i, feat in enumerate(TEMPORAL_FEATURES):
    r, c = divmod(i, 5)
    fig_norm.add_trace(go.Histogram(x=df_temp_scaled[feat].dropna(),
        nbinsx=40, marker_color="#1F77B4", name=feat, showlegend=False),
        row=r+1, col=c+1)
fig_norm.update_layout(title="Temporal Features After Normalisation",
    height=600, template="plotly_white")
fig_norm.write_html(f"{OUTPUT_DIR}/03_normalisation_check.html")

print("\nPhase 4 complete.")
print(f"  X_static:   {X_static.shape}")
print(f"  X_temporal: {X_temporal.shape}")
print(f"  y_severity: {y_severity_mapped.shape}  classes: {len(severity_map)}")
print(f"Saved numpy tensors → {DATA_DIR}/")
print(f"Saved charts → {OUTPUT_DIR}/")