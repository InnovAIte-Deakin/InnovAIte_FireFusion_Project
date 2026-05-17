"""
FireFusion — Phase 2: Exploratory Data Analysis
================================================
Generates distribution plots, correlation matrix, feature evolution
across timesteps, diurnal patterns, and target label analysis.

Outputs:
    outputs/02_eda/01_distributions.png/.html
    outputs/02_eda/02_correlation_matrix.png/.html
    outputs/02_eda/03_feature_evolution.png/.html
    outputs/02_eda/04_diurnal_patterns.png/.html
    outputs/02_eda/05_target_labels.png/.html
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

DATA_DIR   = "data"
OUTPUT_DIR = "outputs/02_eda"
os.makedirs(OUTPUT_DIR, exist_ok=True)

STATIC_FEATURES   = ["elevation_m","slope_deg","aspect_deg","dist_to_water_m",
                      "veg_type_encoded","ndvi_at_ignition","ndwi_at_ignition","nbr_at_ignition"]
TEMPORAL_FEATURES = ["max_temp_c","wind_speed_kmh","wind_dir_deg","rel_humidity_pct",
                      "precipitation_mm","evapotranspiration","soil_moisture",
                      "soil_temp_c","days_since_rain","years_since_last_fire"]
TARGET_LABELS     = ["severity_class","area_ha_burned","rate_of_spread_ha_per_day"]
PALETTE           = {2:"#74C476", 3:"#FDB913", 4:"#F97F08", 5:"#D62728"}

print("Loading data...")
df      = pd.read_csv(f"{DATA_DIR}/data_flat.csv")
df_temp = pd.read_csv(f"{DATA_DIR}/data_temporal.csv")
df["severity_class"] = df["severity_class"].astype(int)
df_temp["severity_class"] = df_temp["severity_class"].astype(int)
print(f"  Flat: {df.shape}   Temporal: {df_temp.shape}")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — Feature distributions
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 1 — Distributions...")

fig, axes = plt.subplots(3, 4, figsize=(20, 14))
fig.suptitle("FireFusion — Static Feature Distributions", fontsize=15, fontweight="bold")
axes = axes.flatten()

ignition_cols = [f"ignition_{f}" for f in TEMPORAL_FEATURES if f"ignition_{f}" in df.columns]
plot_cols = STATIC_FEATURES[:8] + ignition_cols[:4]

for i, col in enumerate(plot_cols[:12]):
    ax = axes[i]
    for sev in sorted(df["severity_class"].unique()):
        subset = df[df["severity_class"] == sev][col].dropna()
        ax.hist(subset, bins=30, alpha=0.5, label=f"Class {sev}",
                color=PALETTE.get(sev, "gray"), density=True)
    ax.set_title(col.replace("ignition_",""), fontsize=10, fontweight="bold")
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=0.3)
    if i == 0:
        ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_distributions.png", dpi=150, bbox_inches="tight")
plt.close()

fig_plotly = make_subplots(rows=3, cols=4,
    subplot_titles=[c.replace("ignition_","") for c in plot_cols[:12]])
for i, col in enumerate(plot_cols[:12]):
    r, c = divmod(i, 4)
    for sev in sorted(df["severity_class"].unique()):
        subset = df[df["severity_class"] == sev][col].dropna()
        fig_plotly.add_trace(go.Histogram(x=subset, name=f"Class {sev}",
            marker_color=PALETTE.get(sev,"gray"), opacity=0.5,
            showlegend=(i == 0), legendgroup=str(sev)), row=r+1, col=c+1)
fig_plotly.update_layout(title="FireFusion — Static Feature Distributions",
    barmode="overlay", height=900, template="plotly_white")
fig_plotly.write_html(f"{OUTPUT_DIR}/01_distributions.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Correlation matrix
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 2 — Correlation matrix...")

corr_cols = STATIC_FEATURES + TARGET_LABELS
corr_data = df[corr_cols].dropna()
corr_matrix = corr_data.corr()

fig, ax = plt.subplots(figsize=(14, 11))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f",
            cmap="RdYlGn", center=0, ax=ax,
            linewidths=0.5, cbar_kws={"shrink": 0.8}, annot_kws={"size": 8})
ax.set_title("FireFusion — Feature Correlation Matrix", fontsize=14, fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_correlation_matrix.png", dpi=150, bbox_inches="tight")
plt.close()

fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdYlGn",
    title="FireFusion — Feature Correlation Matrix", aspect="auto",
    color_continuous_midpoint=0)
fig_corr.write_html(f"{OUTPUT_DIR}/02_correlation_matrix.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 3 — Feature evolution across timesteps
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 3 — Feature evolution...")

KEY_TEMPORAL = ["max_temp_c","wind_speed_kmh","rel_humidity_pct",
                "soil_moisture","evapotranspiration","days_since_rain"]

df_temp["timestep_label"] = df_temp["day"].astype(str) + "d/" + df_temp["hour"].astype(str) + "h"
timestep_order = (df_temp[["day","hour","timestep_label"]]
                  .drop_duplicates()
                  .sort_values(["day","hour"])["timestep_label"].tolist())

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("FireFusion — Feature Evolution Toward Ignition Day",
             fontsize=14, fontweight="bold")
axes = axes.flatten()

for i, feat in enumerate(KEY_TEMPORAL):
    ax = axes[i]
    for sev in sorted(df_temp["severity_class"].unique()):
        grp = (df_temp[df_temp["severity_class"] == sev]
               .groupby("timestep_label")[feat]
               .mean()
               .reindex(timestep_order))
        ax.plot(range(len(timestep_order)), grp.values,
                marker="o", label=f"Class {sev}",
                color=PALETTE.get(sev,"gray"), linewidth=2)
    ax.set_title(feat, fontweight="bold", fontsize=10)
    ax.set_xticks(range(len(timestep_order)))
    ax.set_xticklabels(timestep_order, rotation=45, ha="right", fontsize=8)
    ax.axvline(x=6, color="red", linestyle="--", alpha=0.5, label="Ignition day")
    ax.grid(alpha=0.3)
    if i == 0:
        ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/03_feature_evolution.png", dpi=150, bbox_inches="tight")
plt.close()

fig_evo = make_subplots(rows=2, cols=3, subplot_titles=KEY_TEMPORAL)
for i, feat in enumerate(KEY_TEMPORAL):
    r, c = divmod(i, 3)
    for sev in sorted(df_temp["severity_class"].unique()):
        grp = (df_temp[df_temp["severity_class"] == sev]
               .groupby("timestep_label")[feat].mean()
               .reindex(timestep_order))
        fig_evo.add_trace(go.Scatter(x=timestep_order, y=grp.values,
            mode="lines+markers", name=f"Class {sev}",
            line=dict(color=PALETTE.get(sev,"gray")),
            showlegend=(i == 0), legendgroup=str(sev)), row=r+1, col=c+1)
fig_evo.update_layout(title="FireFusion — Feature Evolution Toward Ignition",
    height=700, template="plotly_white")
fig_evo.write_html(f"{OUTPUT_DIR}/03_feature_evolution.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 4 — Diurnal patterns (06:00 vs 18:00)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 4 — Diurnal patterns...")

diurnal_feats = ["max_temp_c","wind_speed_kmh","rel_humidity_pct","soil_temp_c"]
morning = df_temp[df_temp["hour"] == 6]
afternoon = df_temp[df_temp["hour"] == 18]

fig, axes = plt.subplots(1, 4, figsize=(20, 6))
fig.suptitle("FireFusion — Diurnal Patterns: Morning (06:00) vs Afternoon (18:00)",
             fontsize=13, fontweight="bold")
for i, feat in enumerate(diurnal_feats):
    ax = axes[i]
    m_vals = morning[feat].dropna()
    a_vals = afternoon[feat].dropna()
    ax.boxplot([m_vals, a_vals], labels=["06:00", "18:00"],
               patch_artist=True,
               boxprops=dict(facecolor="#AEC6E8"),
               medianprops=dict(color="navy", linewidth=2))
    ax.set_title(feat, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    diff = a_vals.mean() - m_vals.mean()
    ax.set_xlabel(f"Δ afternoon−morning: {diff:+.2f}", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/04_diurnal_patterns.png", dpi=150, bbox_inches="tight")
plt.close()

fig_d = make_subplots(rows=1, cols=4, subplot_titles=diurnal_feats)
for i, feat in enumerate(diurnal_feats):
    fig_d.add_trace(go.Box(y=morning[feat].dropna(), name="06:00",
        marker_color="#AEC6E8", showlegend=(i==0), legendgroup="06"), row=1, col=i+1)
    fig_d.add_trace(go.Box(y=afternoon[feat].dropna(), name="18:00",
        marker_color="#F4845F", showlegend=(i==0), legendgroup="18"), row=1, col=i+1)
fig_d.update_layout(title="Diurnal Patterns: Morning vs Afternoon",
    height=500, template="plotly_white", boxmode="group")
fig_d.write_html(f"{OUTPUT_DIR}/04_diurnal_patterns.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 5 — Target label analysis
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 5 — Target labels...")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("FireFusion — Target Label Distributions", fontsize=14, fontweight="bold")

# Severity class bar chart
sev_counts = df["severity_class"].value_counts().sort_index()
colors = [PALETTE.get(s, "gray") for s in sev_counts.index]
axes[0].bar(sev_counts.index.astype(str), sev_counts.values, color=colors, edgecolor="white")
axes[0].set_title("Severity Class Distribution", fontweight="bold")
axes[0].set_xlabel("Severity Class")
axes[0].set_ylabel("Count")
for j, (x, v) in enumerate(zip(sev_counts.index, sev_counts.values)):
    axes[0].text(j, v + 20, f"{v/len(df)*100:.1f}%", ha="center", fontsize=9)
axes[0].grid(axis="y", alpha=0.3)

# Area burned — log scale
axes[1].hist(np.log1p(df["area_ha_burned"]), bins=50, color="#E07B39", edgecolor="white")
axes[1].set_title("Area Burned (log scale)", fontweight="bold")
axes[1].set_xlabel("log(1 + area_ha_burned)")
axes[1].set_ylabel("Count")
axes[1].grid(axis="y", alpha=0.3)

# Rate of spread
axes[2].hist(df["rate_of_spread_ha_per_day"], bins=50, color="#5B8DB8", edgecolor="white")
axes[2].set_title("Rate of Spread (ha/day)", fontweight="bold")
axes[2].set_xlabel("rate_of_spread_ha_per_day")
axes[2].set_ylabel("Count")
axes[2].grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/05_target_labels.png", dpi=150, bbox_inches="tight")
plt.close()

fig_t = make_subplots(rows=1, cols=3,
    subplot_titles=["Severity Class Distribution","Area Burned (log)","Rate of Spread"])
fig_t.add_trace(go.Bar(x=sev_counts.index.astype(str), y=sev_counts.values,
    marker_color=colors, name="Count"), row=1, col=1)
fig_t.add_trace(go.Histogram(x=np.log1p(df["area_ha_burned"]),
    nbinsx=50, marker_color="#E07B39", name="Area"), row=1, col=2)
fig_t.add_trace(go.Histogram(x=df["rate_of_spread_ha_per_day"],
    nbinsx=50, marker_color="#5B8DB8", name="RoS"), row=1, col=3)
fig_t.update_layout(title="FireFusion — Target Label Distributions",
    height=500, template="plotly_white", showlegend=False)
fig_t.write_html(f"{OUTPUT_DIR}/05_target_labels.html")

print("\nPhase 2 complete.")
print(f"Saved 5 charts (PNG + HTML) → {OUTPUT_DIR}/")