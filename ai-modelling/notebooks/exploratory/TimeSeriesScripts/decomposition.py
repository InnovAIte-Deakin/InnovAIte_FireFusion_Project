"""
FireFusion — Phase 3: Temporal Decomposition & Seasonality
===========================================================
Performs STL decomposition, ACF/PACF analysis, ADF stationarity
testing, and diurnal deseasoning on the 8-step weather sequence.

Outputs:
    outputs/03_decomposition/01_stl_decomposition.png/.html
    outputs/03_decomposition/02_acf_pacf.png/.html
    outputs/03_decomposition/03_stationarity_report.txt
    outputs/03_decomposition/04_deseasoned.png/.html
    data/data_deseasoned.csv
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller, acf, pacf
warnings.filterwarnings("ignore")

DATA_DIR   = "data"
OUTPUT_DIR = "outputs/03_decomposition"
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEY_FEATURES = ["max_temp_c","wind_speed_kmh","rel_humidity_pct",
                "soil_moisture","evapotranspiration","days_since_rain"]

print("Loading temporal data...")
df_temp = pd.read_csv(f"{DATA_DIR}/data_temporal.csv")
df_flat = pd.read_csv(f"{DATA_DIR}/data_flat.csv")
df_temp["severity_class"] = df_temp["severity_class"].astype(int)

# ── Build mean sequence across all records ─────────────────────────────────
df_temp["timestep_idx"] = (df_temp["day"] + 3) * 2 + (df_temp["hour"] == 18).astype(int)
mean_seq = df_temp.groupby("timestep_idx")[KEY_FEATURES].mean()
print(f"  Mean sequence shape: {mean_seq.shape}")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — STL Decomposition
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 1 — STL Decomposition...")

fig, axes = plt.subplots(len(KEY_FEATURES), 4, figsize=(22, 18))
fig.suptitle("FireFusion — STL Decomposition of Weather Sequence",
             fontsize=14, fontweight="bold")

stl_results = {}
for i, feat in enumerate(KEY_FEATURES):
    series = mean_seq[feat].values
    # STL requires period — use 2 (diurnal cycle: 06:00 and 18:00)
    try:
        stl = STL(series, period=2, robust=True)
        result = stl.fit()
        stl_results[feat] = result
        components = [series, result.trend, result.seasonal, result.resid]
        labels = ["Observed","Trend","Seasonal (diurnal)","Residual"]
        colors = ["#1F77B4","#FF7F0E","#2CA02C","#D62728"]
        for j, (comp, lbl, col) in enumerate(zip(components, labels, colors)):
            axes[i][j].plot(comp, color=col, linewidth=1.8, marker="o", markersize=4)
            if i == 0:
                axes[i][j].set_title(lbl, fontweight="bold", fontsize=10)
            if j == 0:
                axes[i][j].set_ylabel(feat, fontsize=9, fontweight="bold")
            axes[i][j].grid(alpha=0.3)
            axes[i][j].set_xticks(range(8))
            axes[i][j].set_xticklabels(
                [f"d{d}h{h}" for d in range(-3,1) for h in [6,18]], rotation=45, fontsize=7)
    except Exception as e:
        axes[i][0].text(0.5, 0.5, f"STL failed:\n{e}", ha="center", va="center",
                        transform=axes[i][0].transAxes, fontsize=8)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_stl_decomposition.png", dpi=150, bbox_inches="tight")
plt.close()

# Plotly version — trend only for clarity
fig_stl = make_subplots(rows=2, cols=3, subplot_titles=KEY_FEATURES)
tstep_labels = [f"d{d}h{h}" for d in range(-3,1) for h in [6,18]]
for i, feat in enumerate(KEY_FEATURES):
    r, c = divmod(i, 3)
    if feat in stl_results:
        res = stl_results[feat]
        fig_stl.add_trace(go.Scatter(x=tstep_labels, y=mean_seq[feat].values,
            mode="lines+markers", name="Observed", line=dict(color="#1F77B4"),
            showlegend=(i==0), legendgroup="obs"), row=r+1, col=c+1)
        fig_stl.add_trace(go.Scatter(x=tstep_labels, y=res.trend,
            mode="lines", name="Trend", line=dict(color="#FF7F0E", dash="dash"),
            showlegend=(i==0), legendgroup="trend"), row=r+1, col=c+1)
fig_stl.update_layout(title="STL Decomposition — Trend vs Observed",
    height=600, template="plotly_white")
fig_stl.write_html(f"{OUTPUT_DIR}/01_stl_decomposition.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — ACF / PACF
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 2 — ACF/PACF...")

fig, axes = plt.subplots(len(KEY_FEATURES), 2, figsize=(14, 18))
fig.suptitle("FireFusion — ACF and PACF of Weather Features",
             fontsize=14, fontweight="bold")

acf_results = {}
for i, feat in enumerate(KEY_FEATURES):
    series = df_temp.groupby(["cell_id","timestep_idx"])[feat].mean().unstack().values.flatten()
    series = series[~np.isnan(series)]

    max_lags = min(20, len(series) // 2 - 1)

    try:
        acf_vals  = acf(series,  nlags=max_lags, fft=True)
        pacf_vals = pacf(series, nlags=max_lags)
        acf_results[feat] = {"acf": acf_vals, "pacf": pacf_vals}

        ci = 1.96 / np.sqrt(len(series))

        # ACF
        axes[i][0].bar(range(len(acf_vals)), acf_vals, color="#1F77B4", alpha=0.7)
        axes[i][0].axhline(y=ci,  color="red", linestyle="--", alpha=0.7)
        axes[i][0].axhline(y=-ci, color="red", linestyle="--", alpha=0.7)
        axes[i][0].axhline(y=0,   color="black", linewidth=0.8)
        axes[i][0].set_ylabel(feat, fontsize=9, fontweight="bold")
        if i == 0:
            axes[i][0].set_title("ACF", fontweight="bold")
        axes[i][0].grid(alpha=0.2)

        # PACF
        axes[i][1].bar(range(len(pacf_vals)), pacf_vals, color="#FF7F0E", alpha=0.7)
        axes[i][1].axhline(y=ci,  color="red", linestyle="--", alpha=0.7)
        axes[i][1].axhline(y=-ci, color="red", linestyle="--", alpha=0.7)
        axes[i][1].axhline(y=0,   color="black", linewidth=0.8)
        if i == 0:
            axes[i][1].set_title("PACF", fontweight="bold")
        axes[i][1].grid(alpha=0.2)
    except Exception as e:
        axes[i][0].text(0.5,0.5,f"Failed: {e}", ha="center", va="center",
                        transform=axes[i][0].transAxes, fontsize=8)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_acf_pacf.png", dpi=150, bbox_inches="tight")
plt.close()

fig_acf = make_subplots(rows=len(KEY_FEATURES), cols=2,
    subplot_titles=[f"{f} ACF/PACF" for f in KEY_FEATURES for _ in range(2)])
for i, feat in enumerate(KEY_FEATURES):
    if feat in acf_results:
        lags = list(range(len(acf_results[feat]["acf"])))
        fig_acf.add_trace(go.Bar(x=lags, y=acf_results[feat]["acf"],
            name=f"{feat} ACF", marker_color="#1F77B4",
            showlegend=False), row=i+1, col=1)
        fig_acf.add_trace(go.Bar(x=lags, y=acf_results[feat]["pacf"],
            name=f"{feat} PACF", marker_color="#FF7F0E",
            showlegend=False), row=i+1, col=2)
fig_acf.update_layout(title="ACF and PACF", height=1200, template="plotly_white")
fig_acf.write_html(f"{OUTPUT_DIR}/02_acf_pacf.html")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — ADF Stationarity Test
# ─────────────────────────────────────────────────────────────────────────────
print("Running ADF stationarity tests...")

report_lines = ["FireFusion — Phase 3 Stationarity Report (ADF Test)", "="*55, "",
                f"{'Feature':<30} {'ADF Stat':>10} {'p-value':>10} {'Stationary?':>12}", "-"*55]

for feat in KEY_FEATURES:
    series = df_temp.groupby("timestep_idx")[feat].mean().values
    try:
        adf_stat, p_val, _, _, _, _ = adfuller(series)
        stationary = "YES" if p_val < 0.05 else "NO"
        report_lines.append(f"{feat:<30} {adf_stat:>10.3f} {p_val:>10.4f} {stationary:>12}")
    except Exception as e:
        report_lines.append(f"{feat:<30} {'ERROR':>10} {str(e)[:20]:>10}")

report_lines += ["", "Interpretation:",
                 "  p < 0.05 → stationary (no unit root, safe for LSTM/Transformer input)",
                 "  p ≥ 0.05 → non-stationary → consider differencing before modelling"]

report_text = "\n".join(report_lines)
print("\n" + report_text)
with open(f"{OUTPUT_DIR}/03_stationarity_report.txt","w") as f:
    f.write(report_text)

# ─────────────────────────────────────────────────────────────────────────────
# CHART 4 — Deseasoning (remove diurnal cycle)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 4 — Deseasoned sequences...")

# Compute diurnal means (morning vs afternoon across all records)
diurnal_means = df_temp.groupby("hour")[KEY_FEATURES].mean()

# Subtract diurnal mean from each timestep
df_deseasoned = df_temp.copy()
for feat in KEY_FEATURES:
    df_deseasoned[f"{feat}_deseasoned"] = (
        df_temp[feat] - df_temp["hour"].map(diurnal_means[feat])
    )

# Plot original vs deseasoned for mean sequence
mean_orig = df_temp.groupby("timestep_idx")[KEY_FEATURES[:4]].mean()
mean_desea = df_deseasoned.groupby("timestep_idx")[
    [f"{f}_deseasoned" for f in KEY_FEATURES[:4]]].mean()

fig, axes = plt.subplots(2, 4, figsize=(20, 10))
fig.suptitle("FireFusion — Original vs Deseasoned (Diurnal Cycle Removed)",
             fontsize=13, fontweight="bold")

for i, feat in enumerate(KEY_FEATURES[:4]):
    axes[0][i].plot(mean_orig[feat].values, marker="o", color="#1F77B4",
                    linewidth=2, label="Original")
    axes[0][i].set_title(feat, fontweight="bold", fontsize=10)
    axes[0][i].set_xticks(range(8))
    axes[0][i].set_xticklabels([f"d{d}h{h}" for d in range(-3,1) for h in [6,18]],
                                rotation=45, fontsize=7)
    axes[0][i].grid(alpha=0.3)
    if i == 0: axes[0][i].set_ylabel("Original", fontweight="bold")

    axes[1][i].plot(mean_desea[f"{feat}_deseasoned"].values, marker="o",
                    color="#2CA02C", linewidth=2, label="Deseasoned")
    axes[1][i].set_xticks(range(8))
    axes[1][i].set_xticklabels([f"d{d}h{h}" for d in range(-3,1) for h in [6,18]],
                                rotation=45, fontsize=7)
    axes[1][i].axhline(y=0, color="red", linestyle="--", alpha=0.5)
    axes[1][i].grid(alpha=0.3)
    if i == 0: axes[1][i].set_ylabel("Deseasoned", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/04_deseasoned.png", dpi=150, bbox_inches="tight")
plt.close()

fig_des = make_subplots(rows=2, cols=4,
    subplot_titles=[f"{f} Original" for f in KEY_FEATURES[:4]] +
                   [f"{f} Deseasoned" for f in KEY_FEATURES[:4]])
tstep_labels = [f"d{d}h{h}" for d in range(-3,1) for h in [6,18]]
for i, feat in enumerate(KEY_FEATURES[:4]):
    fig_des.add_trace(go.Scatter(x=tstep_labels, y=mean_orig[feat].values,
        mode="lines+markers", line=dict(color="#1F77B4"),
        name=feat, showlegend=False), row=1, col=i+1)
    fig_des.add_trace(go.Scatter(x=tstep_labels,
        y=mean_desea[f"{feat}_deseasoned"].values,
        mode="lines+markers", line=dict(color="#2CA02C"),
        name=f"{feat} deseasoned", showlegend=False), row=2, col=i+1)
fig_des.update_layout(title="Original vs Deseasoned Sequences",
    height=600, template="plotly_white")
fig_des.write_html(f"{OUTPUT_DIR}/04_deseasoned.html")

# Save deseasoned data
df_deseasoned.to_csv(f"{DATA_DIR}/data_deseasoned.csv", index=False)

print("\nPhase 3 complete.")
print(f"Saved 4 charts (PNG + HTML) + stationarity report → {OUTPUT_DIR}/")
print(f"Saved → {DATA_DIR}/data_deseasoned.csv")