"""
FireFusion — Phase 8: Benchmarking Report
==========================================
Consolidates all model results into a comprehensive benchmarking
report comparing baseline and deep learning architectures across
all metrics. Produces final charts and a ranked comparison table.

Outputs:
    outputs/08_benchmark/01_accuracy_comparison.png/.html
    outputs/08_benchmark/02_regression_comparison.png/.html
    outputs/08_benchmark/03_radar_chart.html
    outputs/08_benchmark/04_inference_speed.png/.html
    outputs/08_benchmark/benchmark_report.txt
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OUTPUT_DIR   = "outputs/08_benchmark"
BASELINE_DIR = "outputs/06_baseline"
MODELS_DIR   = "outputs/07_models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load all results ───────────────────────────────────────────────────────
print("Loading results...")
with open(f"{BASELINE_DIR}/baseline_results.json") as f:
    baseline_results = json.load(f)
with open(f"{MODELS_DIR}/all_results.json") as f:
    dl_results = json.load(f)

# Normalise baseline structure to match DL structure
def normalise_baseline(name, res):
    return {
        "severity":   res["severity"],
        "area":       res["area_ha_log"],
        "ros":        res["rate_of_spread"],
        "inference_time_s": res["severity"].get("inference_time_s", 0.001),
        "ms_per_sample":    res["severity"].get("inference_time_s", 0.001) * 1000,
        "train_time_s": res.get("train_time_s", 0),
        "type": "baseline"
    }

all_results = {
    "Persistence":    normalise_baseline("Persistence",    baseline_results["persistence"]),
    "Logistic/Ridge": normalise_baseline("Logistic/Ridge", baseline_results["logistic_ridge"]),
    "Random Forest":  normalise_baseline("Random Forest",  baseline_results["random_forest"]),
}
for k, v in dl_results.items():
    v["type"] = "deep_learning"
    all_results[k] = v

MODEL_NAMES = list(all_results.keys())
COLORS_TYPE = {"baseline": "#AEC6E8", "deep_learning": "#F4845F"}
COLORS_MODEL = {
    "Persistence":    "#CCCCCC",
    "Logistic/Ridge": "#74C476",
    "Random Forest":  "#FDB913",
    "LSTM":           "#1F77B4",
    "Transformer":    "#FF7F0E",
    "CNN-LSTM":       "#2CA02C",
    "TCN":            "#D62728",
}

# ── Build summary dataframe ────────────────────────────────────────────────
rows = []
for name, res in all_results.items():
    rows.append({
        "Model":         name,
        "Type":          res["type"],
        "Severity Acc":  res["severity"]["accuracy"],
        "Severity F1":   res["severity"]["f1_weighted"],
        "Area MAE":      res["area"]["mae"],
        "Area RMSE":     res["area"]["rmse"],
        "Area R²":       res["area"]["r2"],
        "RoS MAE":       res["ros"]["mae"],
        "RoS RMSE":      res["ros"]["rmse"],
        "RoS R²":        res["ros"]["r2"],
        "Inf Time (ms)": round(res.get("ms_per_sample", 0), 3),
        "Train Time (s)":round(res.get("train_time_s", 0), 1),
    })
df = pd.DataFrame(rows)
df_sorted = df.sort_values("Severity Acc", ascending=False)

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — Accuracy and F1 comparison
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 1 — Accuracy comparison...")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("FireFusion — Model Benchmarking: Severity Classification",
             fontsize=14, fontweight="bold")

colors = [COLORS_MODEL[n] for n in df_sorted["Model"]]
x = range(len(df_sorted))

for ax, metric, title in zip(axes,
    ["Severity Acc","Severity F1"],
    ["Accuracy (Test Set)","Weighted F1 Score (Test Set)"]):
    bars = ax.bar(x, df_sorted[metric], color=colors, edgecolor="white", width=0.6)
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted["Model"], rotation=30, ha="right", fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.axhline(y=df_sorted[df_sorted["Model"]=="Persistence"][metric].values[0],
               color="gray", linestyle="--", alpha=0.6, label="Persistence baseline")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, df_sorted[metric]):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.01, f"{val:.3f}",
                ha="center", fontsize=8, fontweight="bold")

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_accuracy_comparison.png", dpi=150, bbox_inches="tight")
plt.close()

fig_acc = make_subplots(rows=1, cols=2,
    subplot_titles=["Severity Accuracy","Weighted F1 Score"])
for i, metric in enumerate(["Severity Acc","Severity F1"]):
    fig_acc.add_trace(go.Bar(
        x=df_sorted["Model"].tolist(),
        y=df_sorted[metric].tolist(),
        marker_color=[COLORS_MODEL[n] for n in df_sorted["Model"]],
        text=[f"{v:.3f}" for v in df_sorted[metric]],
        textposition="outside",
        showlegend=False
    ), row=1, col=i+1)
fig_acc.update_yaxes(range=[0, 1.05])
fig_acc.update_layout(title="Severity Classification Comparison",
    height=500, template="plotly_white")
fig_acc.write_html(f"{OUTPUT_DIR}/01_accuracy_comparison.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Regression metrics comparison
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 2 — Regression comparison...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("FireFusion — Regression Metrics Comparison",
             fontsize=14, fontweight="bold")

colors = [COLORS_MODEL[n] for n in df_sorted["Model"]]
x = range(len(df_sorted))

metrics_config = [
    ("Area MAE",  "Area MAE (lower=better)",  False),
    ("Area RMSE", "Area RMSE (lower=better)", False),
    ("Area R²",   "Area R² (higher=better)",  True),
    ("RoS MAE",   "RoS MAE (lower=better)",   False),
    ("RoS RMSE",  "RoS RMSE (lower=better)",  False),
    ("RoS R²",    "RoS R² (higher=better)",   True),
]
for ax, (metric, title, higher_better) in zip(axes.flatten(), metrics_config):
    bars = ax.bar(x, df_sorted[metric], color=colors, edgecolor="white", width=0.6)
    ax.set_title(title, fontweight="bold", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted["Model"], rotation=30, ha="right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars, df_sorted[metric]):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + abs(df_sorted[metric].max()) * 0.01,
                f"{val:.3f}", ha="center", fontsize=7)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/02_regression_comparison.png", dpi=150, bbox_inches="tight")
plt.close()

fig_reg = make_subplots(rows=2, cols=3,
    subplot_titles=[m[1] for m in metrics_config])
for i, (metric, title, _) in enumerate(metrics_config):
    r, c = divmod(i, 3)
    fig_reg.add_trace(go.Bar(
        x=df_sorted["Model"].tolist(),
        y=df_sorted[metric].tolist(),
        marker_color=[COLORS_MODEL[n] for n in df_sorted["Model"]],
        text=[f"{v:.3f}" for v in df_sorted[metric]],
        textposition="outside", showlegend=False
    ), row=r+1, col=c+1)
fig_reg.update_layout(title="Regression Metrics Comparison",
    height=700, template="plotly_white")
fig_reg.write_html(f"{OUTPUT_DIR}/02_regression_comparison.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 3 — Radar chart (DL models only)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 3 — Radar chart...")

dl_df = df[df["Type"] == "deep_learning"].copy()

# Normalise metrics 0-1 for radar (higher = better for all)
radar_metrics = {
    "Severity Acc":  (True,  0, 1),
    "Severity F1":   (True,  0, 1),
    "Area R²":       (True, -0.2, 0.5),
    "RoS R²":        (True,  0, 0.4),
    "Speed (inv)":   (True,  0, 1),   # inverse of inference time
}
dl_df["Speed (inv)"] = 1 - (dl_df["Inf Time (ms)"] /
                              dl_df["Inf Time (ms)"].max())

def norm(series, lo, hi):
    return ((series - lo) / (hi - lo)).clip(0, 1)

categories = list(radar_metrics.keys())
fig_radar = go.Figure()
for _, row in dl_df.iterrows():
    vals = [norm(pd.Series([row[m]]), lo, hi).values[0]
            for m, (higher, lo, hi) in radar_metrics.items()]
    vals += [vals[0]]   # close the polygon
    fig_radar.add_trace(go.Scatterpolar(
        r=vals, theta=categories + [categories[0]],
        fill="toself", name=row["Model"],
        line=dict(color=COLORS_MODEL[row["Model"]])
    ))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    title="Deep Learning Models — Normalised Performance Radar",
    template="plotly_white", height=500
)
fig_radar.write_html(f"{OUTPUT_DIR}/03_radar_chart.html")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 4 — Inference speed comparison
# ─────────────────────────────────────────────────────────────────────────────
print("Generating Chart 4 — Inference speed...")

fig, ax = plt.subplots(figsize=(12, 5))
colors = [COLORS_MODEL[n] for n in df_sorted["Model"]]
bars = ax.bar(range(len(df_sorted)), df_sorted["Inf Time (ms)"],
              color=colors, edgecolor="white", width=0.6)
ax.set_title("FireFusion — Inference Speed per Sample (ms)",
             fontsize=13, fontweight="bold")
ax.set_xticks(range(len(df_sorted)))
ax.set_xticklabels(df_sorted["Model"], rotation=30, ha="right")
ax.set_ylabel("Milliseconds per sample")
ax.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, df_sorted["Inf Time (ms)"]):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.001,
            f"{val:.3f}ms", ha="center", fontsize=9, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/04_inference_speed.png", dpi=150, bbox_inches="tight")
plt.close()

fig_spd = go.Figure(go.Bar(
    x=df_sorted["Model"].tolist(),
    y=df_sorted["Inf Time (ms)"].tolist(),
    marker_color=[COLORS_MODEL[n] for n in df_sorted["Model"]],
    text=[f"{v:.3f}ms" for v in df_sorted["Inf Time (ms)"]],
    textposition="outside"
))
fig_spd.update_layout(title="Inference Speed per Sample",
    yaxis_title="ms / sample", template="plotly_white", height=450)
fig_spd.write_html(f"{OUTPUT_DIR}/04_inference_speed.html")

# ─────────────────────────────────────────────────────────────────────────────
# TEXT REPORT
# ─────────────────────────────────────────────────────────────────────────────
print("Generating benchmark report...")

best_acc   = df.loc[df["Severity Acc"].idxmax(), "Model"]
best_f1    = df.loc[df["Severity F1"].idxmax(), "Model"]
best_ar2   = df.loc[df["Area R²"].idxmax(), "Model"]
best_rosr2 = df.loc[df["RoS R²"].idxmax(), "Model"]
fastest    = df.loc[df["Inf Time (ms)"].idxmin(), "Model"]

report_lines = [
    "FireFusion — Phase 8 Benchmarking Report",
    "="*65,
    "NOTE: Results are on SYNTHETIC data (5000 records, seed=42).",
    "      Intended as proof-of-concept pipeline validation only.",
    "      Final evaluation will use real Victorian fire data.",
    "="*65, "",
    "── Full Results Table ────────────────────────────────────────────",
    f"{'Model':<18} {'Acc':>6} {'F1':>6} {'Ar.MAE':>8} {'Ar.R²':>7} "
    f"{'RoS MAE':>8} {'RoS R²':>7} {'Inf(ms)':>8} {'Train(s)':>9}",
    "-"*65,
]
for _, row in df_sorted.iterrows():
    report_lines.append(
        f"{row['Model']:<18} {row['Severity Acc']:>6.4f} {row['Severity F1']:>6.4f} "
        f"{row['Area MAE']:>8.4f} {row['Area R²']:>7.4f} "
        f"{row['RoS MAE']:>8.4f} {row['RoS R²']:>7.4f} "
        f"{row['Inf Time (ms)']:>8.3f} {row['Train Time (s)']:>9.1f}"
    )

report_lines += [
    "",
    "── Winners by Category ───────────────────────────────────────────",
    f"  Best severity accuracy : {best_acc}",
    f"  Best severity F1       : {best_f1}",
    f"  Best area R²           : {best_ar2}",
    f"  Best RoS R²            : {best_rosr2}",
    f"  Fastest inference      : {fastest}",
    "",
    "── Analysis ──────────────────────────────────────────────────────",
    "  Transformer achieved the highest severity classification accuracy",
    "  on this synthetic dataset, outperforming the Random Forest baseline.",
    "  TCN produced the best regression results (area R²) with competitive",
    "  classification performance and fast inference.",
    "",
    "  LSTM and CNN-LSTM underperformed relative to baselines, likely due",
    "  to the short 8-step sequence (insufficient temporal depth for LSTM",
    "  to outperform simpler models on this synthetic dataset size).",
    "",
    "  Logistic Regression performed surprisingly well (79.7% accuracy),",
    "  suggesting the synthetic data has strong linear separability by",
    "  design — expected given the FFDI-based label derivation formula.",
    "",
    "── Recommendation (synthetic data) ──────────────────────────────",
    "  Primary candidate  : Transformer (best severity accuracy + fast inference)",
    "  Secondary candidate: TCN (best regression + competitive classification)",
    "  Baseline to beat   : Logistic Regression (79.7% accuracy)",
    "",
    "── Next Steps ────────────────────────────────────────────────────",
    "  1. Replace synthetic data with real Victorian fire history +",
    "     weather enrichment dataset",
    "  2. Re-run full pipeline on real data",
    "  3. Validate against FESM ground truth labels",
    "  4. Tune Transformer and TCN hyperparameters on real data",
    "="*65,
]
report_text = "\n".join(report_lines)
print("\n" + report_text)
with open(f"{OUTPUT_DIR}/benchmark_report.txt","w") as f:
    f.write(report_text)

df_sorted.to_csv(f"{OUTPUT_DIR}/benchmark_table.csv", index=False)

print(f"\nPhase 8 complete.")
print(f"Saved charts + report → {OUTPUT_DIR}/")