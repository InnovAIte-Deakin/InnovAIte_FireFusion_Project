"""
FireFusion — Phase 1: Data Loading & Structural Validation
===========================================================
Loads the GeoJSON training file, flattens nested structure into
a long-format dataframe, validates tensor integrity, and saves
a clean CSV ready for all downstream phases.

Output:
    data/data_flat.csv          — flat dataframe, one row per record
    data/data_temporal.csv      — long format, one row per timestep
    outputs/01_validation_report.txt
"""

import json
import os
import geopandas as gpd
import pandas as pd
import numpy as np

# ── Config ─────────────────────────────────────────────────────────────────
INPUT_FILE     = "firefusion_training.geojson"
DATA_DIR       = "data"
OUTPUT_DIR     = "outputs/01_validation"
EXPECTED_TIMESTEPS     = 8
EXPECTED_STATIC_FEATS  = 8
EXPECTED_TEMPORAL_FEATS= 10

STATIC_FEATURES  = ["elevation_m","slope_deg","aspect_deg","dist_to_water_m",
                     "veg_type_encoded","ndvi_at_ignition","ndwi_at_ignition","nbr_at_ignition"]
TEMPORAL_FEATURES= ["max_temp_c","wind_speed_kmh","wind_dir_deg","rel_humidity_pct",
                     "precipitation_mm","evapotranspiration","soil_moisture",
                     "soil_temp_c","days_since_rain","years_since_last_fire"]
TARGET_LABELS    = ["severity_class","area_ha_burned","rate_of_spread_ha_per_day"]
FEATURE_RANGES   = {
    "elevation_m":        (0, 1986),
    "slope_deg":          (0, 45),
    "aspect_deg":         (0, 360),
    "dist_to_water_m":    (0, 50000),
    "veg_type_encoded":   (1, 6),
    "ndvi_at_ignition":   (-1, 1),
    "ndwi_at_ignition":   (-1, 1),
    "nbr_at_ignition":    (-1, 1),
    "max_temp_c":         (0, 55),
    "wind_speed_kmh":     (0, 150),
    "wind_dir_deg":       (0, 360),
    "rel_humidity_pct":   (0, 100),
    "precipitation_mm":   (0, 200),
    "evapotranspiration": (0, 20),
    "soil_moisture":      (0, 1),
    "soil_temp_c":        (0, 65),
    "days_since_rain":    (0, 365),
    "years_since_last_fire": (0, 100),
    "severity_class":     (1, 5),
    "area_ha_burned":     (0, 200000),
    "rate_of_spread_ha_per_day": (0, 5000),
}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load ───────────────────────────────────────────────────────────────────
print("Loading GeoJSON...")
gdf = gpd.read_file(INPUT_FILE)
print(f"  Records loaded: {len(gdf)}")

# ── Flatten ────────────────────────────────────────────────────────────────
print("Flattening nested structure...")

flat_rows   = []
temporal_rows = []

for idx, row in gdf.iterrows():
    props = row

    # Root fields
    base = {
        "cell_id":          props.get("cell_id"),
        "cell_area_ha":     props.get("cell_area_ha"),
        "grid_resolution_m":props.get("grid_resolution_m"),
        "lon":              row.geometry.x if row.geometry else None,
        "lat":              row.geometry.y if row.geometry else None,
    }

    # Static terrain
    terrain = props.get("static_terrain") or {}
    if isinstance(terrain, str):
        terrain = json.loads(terrain)
    for k in ["elevation_m","slope_deg","aspect_deg","dist_to_water_m"]:
        base[k] = terrain.get(k)

    # Biological fuel
    fuel = props.get("biological_fuel") or {}
    if isinstance(fuel, str):
        fuel = json.loads(fuel)
    for k in ["veg_type_encoded","ndvi_at_ignition","ndwi_at_ignition","nbr_at_ignition"]:
        base[k] = fuel.get(k)

    # Historical fire
    hist = props.get("historical_fire") or {}
    if isinstance(hist, str):
        hist = json.loads(hist)
    for k in ["years_since_last_fire","fire_frequency","last_fire_area_ha","last_fire_severity"]:
        base[k] = hist.get(k)

    # Target labels
    labels = props.get("target_labels") or {}
    if isinstance(labels, str):
        labels = json.loads(labels)
    for k in TARGET_LABELS:
        base[k] = labels.get(k)

    # Weather sequence — flatten ignition-day peak (day=0, hour=18) into flat row
    weather = props.get("weather_sequence") or {}
    if isinstance(weather, str):
        weather = json.loads(weather)
    timesteps = weather.get("timesteps", [])

    base["n_timesteps"] = len(timesteps)

    for step in timesteps:
        if step.get("day") == 0 and step.get("hour") == 18:
            for k in TEMPORAL_FEATURES:
                base[f"ignition_{k}"] = step.get(k)

    flat_rows.append(base)

    # Long-format temporal rows
    for step in timesteps:
        t_row = {"cell_id": base["cell_id"], "severity_class": base["severity_class"]}
        t_row["day"]  = step.get("day")
        t_row["hour"] = step.get("hour")
        for k in TEMPORAL_FEATURES:
            t_row[k] = step.get(k)
        temporal_rows.append(t_row)

df       = pd.DataFrame(flat_rows)
df_temp  = pd.DataFrame(temporal_rows)

print(f"  Flat dataframe shape:     {df.shape}")
print(f"  Temporal dataframe shape: {df_temp.shape}")

# ── Validation ─────────────────────────────────────────────────────────────
print("\nRunning validation checks...")
report_lines = ["FireFusion — Phase 1 Validation Report", "="*55, ""]

errors   = []
warnings = []

# 1. Tensor shape integrity
ts_counts = df["n_timesteps"].value_counts()
if len(ts_counts) == 1 and ts_counts.index[0] == EXPECTED_TIMESTEPS:
    report_lines.append(f"[PASS] All {len(df)} records have exactly {EXPECTED_TIMESTEPS} timesteps")
else:
    errors.append(f"[FAIL] Inconsistent timestep counts: {ts_counts.to_dict()}")

# 2. Null checks
null_counts = df[STATIC_FEATURES + TARGET_LABELS].isnull().sum()
null_issues = null_counts[null_counts > 0]
if null_issues.empty:
    report_lines.append("[PASS] No null values in static features or target labels")
else:
    for col, cnt in null_issues.items():
        warnings.append(f"[WARN] {col}: {cnt} nulls ({cnt/len(df)*100:.1f}%)")

# 3. Range checks
range_errors = []
all_check_cols = {**{f: FEATURE_RANGES[f] for f in STATIC_FEATURES if f in FEATURE_RANGES},
                  **{f: FEATURE_RANGES[f] for f in TARGET_LABELS if f in FEATURE_RANGES}}
for col, (lo, hi) in all_check_cols.items():
    if col in df.columns:
        out_of_range = ((df[col] < lo) | (df[col] > hi)).sum()
        if out_of_range > 0:
            range_errors.append(f"[FAIL] {col}: {out_of_range} values outside [{lo}, {hi}]")
if range_errors:
    errors.extend(range_errors)
else:
    report_lines.append("[PASS] All static features and labels within valid ranges")

# 4. Severity class completeness
sev_classes = sorted(df["severity_class"].dropna().unique())
report_lines.append(f"[INFO] Severity classes present: {sev_classes}")

# 5. Duplicate cell IDs
dupes = df["cell_id"].duplicated().sum()
if dupes == 0:
    report_lines.append("[PASS] No duplicate cell IDs")
else:
    warnings.append(f"[WARN] {dupes} duplicate cell IDs found")

# 6. Summary stats
report_lines += [
    "",
    "── Summary Statistics ──────────────────────────────",
    f"Total records:        {len(df)}",
    f"Static features:      {len(STATIC_FEATURES)}",
    f"Temporal features:    {len(TEMPORAL_FEATURES)}",
    f"Timesteps per record: {EXPECTED_TIMESTEPS} (4 days × 2 steps)",
    "",
    "Severity distribution:",
]
for s in sorted(df["severity_class"].dropna().unique()):
    count = (df["severity_class"] == s).sum()
    report_lines.append(f"  Class {int(s)}: {count:>5} ({count/len(df)*100:.1f}%)")

report_lines += [
    "",
    f"Area burned — min: {df['area_ha_burned'].min():.1f} ha  "
    f"median: {df['area_ha_burned'].median():.1f} ha  "
    f"max: {df['area_ha_burned'].max():.1f} ha",
    f"Rate of spread — min: {df['rate_of_spread_ha_per_day'].min():.1f}  "
    f"median: {df['rate_of_spread_ha_per_day'].median():.1f}  "
    f"max: {df['rate_of_spread_ha_per_day'].max():.1f} ha/day",
    "",
    "── Errors & Warnings ───────────────────────────────",
]
if errors:
    report_lines += errors
if warnings:
    report_lines += warnings
if not errors and not warnings:
    report_lines.append("[PASS] No errors or warnings.")

report_lines += ["", "="*55,
                 f"Status: {'FAILED' if errors else 'PASSED'}",
                 f"Errors: {len(errors)}   Warnings: {len(warnings)}"]

report_text = "\n".join(report_lines)
print("\n" + report_text)

# ── Save ───────────────────────────────────────────────────────────────────
df.to_csv(f"{DATA_DIR}/data_flat.csv", index=False)
df_temp.to_csv(f"{DATA_DIR}/data_temporal.csv", index=False)

with open(f"{OUTPUT_DIR}/validation_report.txt", "w") as f:
    f.write(report_text)

print(f"\nSaved → {DATA_DIR}/data_flat.csv")
print(f"Saved → {DATA_DIR}/data_temporal.csv")
print(f"Saved → {OUTPUT_DIR}/validation_report.txt")