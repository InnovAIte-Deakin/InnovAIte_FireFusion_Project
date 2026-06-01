"""
FireFusion — Phase 5: Train / Test / Holdout Split
===================================================
Splits data into train (70%), test (20%), holdout (10%).
Stratified by severity class to ensure all classes in each set.

Outputs:
    data/splits/X_static_{train,test,holdout}.npy
    data/splits/X_temporal_{train,test,holdout}.npy
    data/splits/y_severity_{train,test,holdout}.npy
    data/splits/y_area_{train,test,holdout}.npy
    data/splits/y_ros_{train,test,holdout}.npy
    outputs/05_split/split_report.txt
    outputs/05_split/01_split_distribution.png/.html
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.model_selection import train_test_split

DATA_DIR   = "data"
SPLIT_DIR  = "data/splits"
OUTPUT_DIR = "outputs/05_split"
os.makedirs(SPLIT_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

PALETTE = {0:"#74C476", 1:"#FDB913", 2:"#F97F08", 3:"#D62728"}

print("Loading tensors...")
X_static   = np.load(f"{DATA_DIR}/X_static.npy")
X_temporal = np.load(f"{DATA_DIR}/X_temporal.npy")
y_severity = np.load(f"{DATA_DIR}/y_severity.npy")
y_area     = np.load(f"{DATA_DIR}/y_area.npy")
y_ros      = np.load(f"{DATA_DIR}/y_ros.npy")

N = len(y_severity)
print(f"  Total records: {N}")
print(f"  X_static:   {X_static.shape}")
print(f"  X_temporal: {X_temporal.shape}")
print(f"  Severity classes: {np.unique(y_severity)}")

# ── Stratified split: 70 / 20 / 10 ───────────────────────────────────────
print("\nSplitting data (70 train / 20 test / 10 holdout) stratified by severity...")

indices = np.arange(N)

# First split: train+test (90%) vs holdout (10%)
idx_traintest, idx_holdout = train_test_split(
    indices, test_size=0.10, random_state=42,
    stratify=y_severity
)

# Second split: train (70%) vs test (20%) from the 90%
idx_train, idx_test = train_test_split(
    idx_traintest, test_size=0.222, random_state=42,   # 0.222 × 90% ≈ 20%
    stratify=y_severity[idx_traintest]
)

print(f"  Train:   {len(idx_train):>5} ({len(idx_train)/N*100:.1f}%)")
print(f"  Test:    {len(idx_test):>5} ({len(idx_test)/N*100:.1f}%)")
print(f"  Holdout: {len(idx_holdout):>5} ({len(idx_holdout)/N*100:.1f}%)")

splits = {"train": idx_train, "test": idx_test, "holdout": idx_holdout}

# ── Save splits ────────────────────────────────────────────────────────────
print("\nSaving splits...")
for split_name, idx in splits.items():
    np.save(f"{SPLIT_DIR}/X_static_{split_name}.npy",   X_static[idx])
    np.save(f"{SPLIT_DIR}/X_temporal_{split_name}.npy", X_temporal[idx])
    np.save(f"{SPLIT_DIR}/y_severity_{split_name}.npy", y_severity[idx])
    np.save(f"{SPLIT_DIR}/y_area_{split_name}.npy",     y_area[idx])
    np.save(f"{SPLIT_DIR}/y_ros_{split_name}.npy",      y_ros[idx])
    print(f"  Saved {split_name}: {len(idx)} records")

# Save indices for reproducibility
np.save(f"{SPLIT_DIR}/idx_train.npy",   idx_train)
np.save(f"{SPLIT_DIR}/idx_test.npy",    idx_test)
np.save(f"{SPLIT_DIR}/idx_holdout.npy", idx_holdout)

# ── Validation report ──────────────────────────────────────────────────────
print("\nGenerating split validation report...")

report_lines = [
    "FireFusion — Phase 5 Split Report", "="*55, "",
    f"Total records : {N}",
    f"Train         : {len(idx_train)} ({len(idx_train)/N*100:.1f}%)",
    f"Test          : {len(idx_test)} ({len(idx_test)/N*100:.1f}%)",
    f"Holdout       : {len(idx_holdout)} ({len(idx_holdout)/N*100:.1f}%)",
    "", "── Severity Class Distribution ─────────────────────",
    f"{'Class':<8} {'Total':>8} {'Train':>8} {'Test':>8} {'Holdout':>8}"
]
for cls in sorted(np.unique(y_severity)):
    total   = (y_severity == cls).sum()
    train_n = (y_severity[idx_train] == cls).sum()
    test_n  = (y_severity[idx_test] == cls).sum()
    hold_n  = (y_severity[idx_holdout] == cls).sum()
    report_lines.append(
        f"{cls:<8} {total:>8} {train_n:>8} {test_n:>8} {hold_n:>8}"
        f"  ({train_n/total*100:.0f}% / {test_n/total*100:.0f}% / {hold_n/total*100:.0f}%)"
    )

report_lines += [
    "", "── Label Statistics ─────────────────────────────────",
    f"{'Statistic':<15} {'Train':>12} {'Test':>12} {'Holdout':>12}",
]
for lbl, arr_name in [("area (mean)", "y_area"), ("area (std)", "y_area"),
                       ("ros (mean)", "y_ros"),  ("ros (std)", "y_ros")]:
    arr = {"y_area": y_area, "y_ros": y_ros}[arr_name]
    fn  = np.mean if "mean" in lbl else np.std
    report_lines.append(
        f"{lbl:<15} "
        f"{fn(arr[idx_train]):>12.3f} "
        f"{fn(arr[idx_test]):>12.3f} "
        f"{fn(arr[idx_holdout]):>12.3f}"
    )

report_text = "\n".join(report_lines)
print("\n" + report_text)
with open(f"{OUTPUT_DIR}/split_report.txt","w") as f:
    f.write(report_text)

# ── Chart 1 — Split distribution ──────────────────────────────────────────
print("\nGenerating Chart 1 — Split distribution...")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("FireFusion — Train / Test / Holdout Severity Distribution",
             fontsize=13, fontweight="bold")

split_labels = ["Train","Test","Holdout"]
split_indices = [idx_train, idx_test, idx_holdout]

for i, (lbl, idx) in enumerate(zip(split_labels, split_indices)):
    classes, counts = np.unique(y_severity[idx], return_counts=True)
    colors = [PALETTE.get(int(c),"gray") for c in classes]
    bars = axes[i].bar([f"Class {int(c)+2}" for c in classes],
                       counts, color=colors, edgecolor="white")
    axes[i].set_title(f"{lbl}  (n={len(idx)})", fontweight="bold")
    axes[i].set_ylabel("Count")
    axes[i].grid(axis="y", alpha=0.3)
    for bar, cnt in zip(bars, counts):
        axes[i].text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + 5,
                     f"{cnt/len(idx)*100:.1f}%",
                     ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/01_split_distribution.png", dpi=150, bbox_inches="tight")
plt.close()

fig_split = make_subplots(rows=1, cols=3,
    subplot_titles=[f"{l} (n={len(i)})" for l, i in zip(split_labels, split_indices)])
for col_i, (lbl, idx) in enumerate(zip(split_labels, split_indices)):
    classes, counts = np.unique(y_severity[idx], return_counts=True)
    fig_split.add_trace(go.Bar(
        x=[f"Class {int(c)+2}" for c in classes],
        y=counts,
        marker_color=[PALETTE.get(int(c),"gray") for c in classes],
        name=lbl, showlegend=False
    ), row=1, col=col_i+1)
fig_split.update_layout(
    title="Train / Test / Holdout Severity Distribution",
    height=450, template="plotly_white"
)
fig_split.write_html(f"{OUTPUT_DIR}/01_split_distribution.html")

print(f"\nPhase 5 complete.")
print(f"Saved splits → {SPLIT_DIR}/")
print(f"Saved charts → {OUTPUT_DIR}/")