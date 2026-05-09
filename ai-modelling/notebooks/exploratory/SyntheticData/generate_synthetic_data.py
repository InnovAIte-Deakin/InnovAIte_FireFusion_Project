"""
FireFusion — Synthetic Training Data Generator
================================================
Generates realistic synthetic bushfire training records for time series forecasting.

Design principles:
- Weather variables follow realistic Victorian summer distributions
- Variables are physically correlated (hot days = low humidity = high ET)
- Lead-up drying sequence builds realistically across 4-day window
- Target labels (severity, area, rate of spread) are derived from input conditions
- Each record represents one 500m grid cell fire event
- Output: GeoJSON training file + JSON inference file

Usage:
    python generate_synthetic_data.py
    python generate_synthetic_data.py --n 500 --seed 99
"""

import json
import math
import random
import argparse
import numpy as np
from datetime import datetime, timezone

# ── Configuration ─────────────────────────────────────────────────────────────
VICTORIA_BBOX     = {"min_lon": 140.9, "max_lon": 149.9,
                      "min_lat": -39.2, "max_lat": -33.9}
GRID_RESOLUTION_M = 500
CELL_AREA_HA      = 25.0
WINDOW_DAYS       = 4
STEPS_PER_DAY     = 2          # 06:00 and 18:00
TOTAL_TIMESTEPS   = WINDOW_DAYS * STEPS_PER_DAY   # 8

# Victorian fire season months (Nov–Apr)
FIRE_SEASON_MONTHS = [11, 12, 1, 2, 3, 4]
FIRE_SEASON_YEARS  = list(range(2000, 2024))

# Vegetation encoding
VEG_TYPES = {1: "Grassland", 2: "Shrubland", 3: "Wet Sclerophyll",
             4: "Dry Sclerophyll", 5: "Rainforest", 6: "Other"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def clamp(value, lo, hi):
    return max(lo, min(hi, value))

def random_date_in_fire_season():
    year  = random.choice(FIRE_SEASON_YEARS)
    month = random.choice(FIRE_SEASON_MONTHS)
    day   = random.randint(1, 28)
    return datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)

def random_vic_point():
    lon = round(random.uniform(VICTORIA_BBOX["min_lon"], VICTORIA_BBOX["max_lon"]), 5)
    lat = round(random.uniform(VICTORIA_BBOX["min_lat"], VICTORIA_BBOX["max_lat"]), 5)
    return lon, lat

def cell_id(index):
    return f"VIC_GRID_{index:05d}"

# ── Static feature generators ─────────────────────────────────────────────────

def generate_static_terrain(lon, lat):
    """
    Elevation increases toward north-east (alpine Victoria).
    Slope correlates loosely with elevation.
    Aspect is random but north-facing (270-360 / 0-90) is more common in fire-prone areas.
    """
    # Elevation: higher in north-east alpine corridor
    base_elev = (lon - 140.9) * 80 + abs(lat + 37) * 120
    elevation = clamp(round(base_elev + random.gauss(0, 80), 1), 0, 1986)

    # Slope increases with elevation
    slope = clamp(round(elevation / 100 * random.uniform(0.5, 1.5) + random.gauss(0, 3), 1), 0, 45)

    # Aspect — uniform distribution, slightly weighted toward north-facing
    if random.random() < 0.35:
        aspect = round(random.uniform(315, 360) if random.random() < 0.5
                       else random.uniform(0, 45), 1)
    else:
        aspect = round(random.uniform(0, 360), 1)

    # Distance to water — lower in wetter east, higher in dry north-west
    dist_water = clamp(round(abs(lon - 146) * 400 + random.gauss(800, 400), 0), 50, 15000)

    return {
        "elevation_m":      elevation,
        "slope_deg":        slope,
        "aspect_deg":       aspect,
        "dist_to_water_m":  dist_water
    }

def generate_biological_fuel(elevation, slope):
    """
    Vegetation type depends on elevation and moisture.
    NDVI / NDWI / NBR are correlated — stressed vegetation has low values on all three.
    Pre-fire stress is higher in drier areas (lower elevation, steeper slope).
    """
    # Vegetation type based on elevation
    if elevation > 900:
        veg = random.choices([3, 5], weights=[0.6, 0.4])[0]        # Wet Sclerophyll / Rainforest
    elif elevation > 400:
        veg = random.choices([3, 4], weights=[0.5, 0.5])[0]        # Wet / Dry Sclerophyll
    elif elevation > 100:
        veg = random.choices([2, 4], weights=[0.4, 0.6])[0]        # Shrubland / Dry Sclerophyll
    else:
        veg = random.choices([1, 2], weights=[0.7, 0.3])[0]        # Grassland / Shrubland

    # Stress level — drier conditions produce lower NDVI/NDWI/NBR
    stress = clamp(random.gauss(0.4, 0.15), 0.1, 0.8)             # 0=unstressed, 1=extreme stress

    ndvi = clamp(round(0.7 - stress * 0.6 + random.gauss(0, 0.05), 3), -0.2, 0.9)
    ndwi = clamp(round(0.2 - stress * 0.5 + random.gauss(0, 0.05), 3), -0.6, 0.4)
    nbr  = clamp(round(0.4 - stress * 0.5 + random.gauss(0, 0.05), 3), -0.3, 0.7)

    return {
        "veg_type_encoded":  veg,
        "ndvi_at_ignition":  ndvi,
        "ndwi_at_ignition":  ndwi,
        "nbr_at_ignition":   nbr,
        "_stress":           stress     # internal — used for label derivation, removed before export
    }

def generate_historical_fire():
    """
    Years since last fire drawn from realistic Victorian distributions.
    Frequently burned areas have lower fire frequency paradoxically
    because they support less accumulated fuel.
    """
    years_since = clamp(round(random.expovariate(1/8) + 1, 1), 0.5, 80)
    fire_freq   = clamp(int(random.gauss(3, 2)), 0, 15)
    last_area   = clamp(round(random.lognormvariate(5, 2), 1), 0.1, 150000)
    last_sev    = clamp(int(random.gauss(3, 1.2)), 1, 5)
    return {
        "years_since_last_fire": years_since,
        "fire_frequency":        fire_freq,
        "last_fire_area_ha":     last_area,
        "last_fire_severity":    last_sev
    }

# ── Weather sequence generator ─────────────────────────────────────────────────

def generate_weather_sequence(ignition_date):
    """
    Generates 8 realistic sub-daily weather timesteps (4 days × 2 steps).
    Physical correlations enforced:
    - Temperature and evapotranspiration are positively correlated
    - Humidity is negatively correlated with temperature
    - Soil moisture depletes over consecutive dry days
    - days_since_rain accumulates realistically
    - Day 0 (ignition day) has the most extreme conditions
    - Afternoon (18:00) is hotter and drier than morning (06:00)
    """

    # Base ignition-day conditions — severe fire weather
    base_temp     = clamp(random.gauss(38, 5), 28, 48)
    base_humidity = clamp(random.gauss(12, 6), 3, 35)
    base_wind     = clamp(random.gauss(45, 15), 15, 100)
    base_wind_dir = round(random.uniform(270, 340), 1)   # NW-erly dominant
    days_since_r  = clamp(int(random.gauss(12, 4)), 4, 30)

    # Soil moisture depletes with days since rain
    base_soil_m   = clamp(round(0.35 - days_since_r * 0.018 + random.gauss(0, 0.02), 3), 0.03, 0.35)
    base_soil_t   = clamp(round(base_temp * 0.9 + random.gauss(0, 2), 1), 20, 55)

    timesteps = []
    day_offsets = list(range(-(WINDOW_DAYS - 1), 1))   # [-3, -2, -1, 0]

    for d_idx, day in enumerate(day_offsets):
        # Conditions intensify as we approach ignition day
        intensity = (d_idx + 1) / WINDOW_DAYS     # 0.25 → 1.0

        for hour in [6, 18]:
            # Morning is cooler and more humid than afternoon
            time_factor = 1.0 if hour == 18 else 0.88

            temp = clamp(round(
                base_temp * intensity * time_factor + random.gauss(0, 1.5), 1), 20, 50)

            humidity = clamp(round(
                base_humidity / (intensity * time_factor) + random.gauss(0, 2), 1), 2, 60)

            wind = clamp(round(
                base_wind * intensity * time_factor + random.gauss(0, 3), 1), 5, 110)

            wind_dir = clamp(round(
                base_wind_dir + random.gauss(0, 15), 1), 0, 360)

            # ET scales with temp and inversely with humidity
            et = clamp(round(
                (temp / 40) * (1 - humidity / 100) * 10 + random.gauss(0, 0.3), 2), 1.0, 15.0)

            # Soil moisture depletes day by day
            soil_factor = 1 - (d_idx * 0.08)
            soil_m = clamp(round(
                base_soil_m * soil_factor + random.gauss(0, 0.005), 3), 0.02, 0.35)

            soil_t = clamp(round(
                base_soil_t * intensity * time_factor + random.gauss(0, 1.5), 1), 18, 58)

            # Rain only possible early in sequence and rarely
            precip = 0.0
            if day < -1 and random.random() < 0.05:
                precip = round(random.uniform(0.2, 5.0), 1)
                days_since_r = 0
            else:
                days_since_r = clamp(days_since_r + 1, 0, 365)

            timesteps.append({
                "day":                day,
                "hour":               hour,
                "max_temp_c":         temp,
                "wind_speed_kmh":     wind,
                "wind_dir_deg":       wind_dir,
                "rel_humidity_pct":   humidity,
                "precipitation_mm":   precip,
                "evapotranspiration": et,
                "soil_moisture":      soil_m,
                "soil_temp_c":        soil_t,
                "days_since_rain":    days_since_r,
            })

    return timesteps

# ── Target label derivation ────────────────────────────────────────────────────

def derive_target_labels(terrain, fuel, historical, weather_seq):
    """
    Derives realistic target labels from input conditions.
    Based on fire behaviour physics:
    - Severity driven by wind, temperature, humidity, slope, fuel stress
    - Area driven by severity and years since last fire (fuel load)
    - Rate of spread driven by wind and slope
    """
    ignition_step = weather_seq[-1]   # day 0, hour 18 — peak conditions

    wind    = ignition_step["wind_speed_kmh"]
    temp    = ignition_step["max_temp_c"]
    hum     = ignition_step["rel_humidity_pct"]
    soil    = ignition_step["soil_moisture"]
    slope   = terrain["slope_deg"]
    stress  = fuel["_stress"]
    yslf    = historical["years_since_last_fire"]

    # Fire danger index (proxy FFDI)
    ffdi = clamp((temp * 0.8 + wind * 0.4 + (100 - hum) * 0.3
                  - soil * 20 + slope * 0.5 + stress * 15), 0, 120)

    # Severity class (1-5)
    if ffdi < 20:   severity = 1
    elif ffdi < 40: severity = 2
    elif ffdi < 60: severity = 3
    elif ffdi < 85: severity = 4
    else:           severity = 5

    # Add some noise to severity
    severity = clamp(severity + random.choices([-1, 0, 0, 0, 1], weights=[1,3,3,3,1])[0], 1, 5)

    # Area burned — driven by severity and fuel accumulation
    fuel_load_factor = clamp(yslf / 10, 0.5, 5.0)
    base_area = math.exp(severity * 1.8) * fuel_load_factor
    area_ha   = clamp(round(base_area * random.lognormvariate(0, 0.5), 1), 0.1, 200000)

    # Rate of spread — wind and slope dominated
    ros = clamp(round(
        (wind * 0.8 + slope * 2.5 + (100 - hum) * 0.3) * (area_ha ** 0.2) / 10
        + random.gauss(0, 20), 1), 1.0, 5000.0)

    return {
        "severity_class":            severity,
        "area_ha_burned":            area_ha,
        "rate_of_spread_ha_per_day": ros
    }

# ── Main generator ─────────────────────────────────────────────────────────────

def generate_record(index, seed=None):
    if seed is not None:
        random.seed(seed + index)
        np.random.seed(seed + index)

    lon, lat    = random_vic_point()
    ign_date    = random_date_in_fire_season()
    terrain     = generate_static_terrain(lon, lat)
    fuel        = generate_biological_fuel(terrain["elevation_m"], terrain["slope_deg"])
    historical  = generate_historical_fire()
    weather_seq = generate_weather_sequence(ign_date)
    labels      = derive_target_labels(terrain, fuel, historical, weather_seq)

    # Add years_since_last_fire to each timestep
    for step in weather_seq:
        step["years_since_last_fire"] = historical["years_since_last_fire"]

    # Remove internal stress key before export
    fuel_clean = {k: v for k, v in fuel.items() if not k.startswith("_")}

    return {
        "cell_id":     cell_id(index),
        "lon":         lon,
        "lat":         lat,
        "ign_date":    ign_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terrain":     terrain,
        "fuel":        fuel_clean,
        "historical":  historical,
        "weather_seq": weather_seq,
        "labels":      labels
    }

# ── Schema serialisers ─────────────────────────────────────────────────────────

def to_training_geojson(records):
    features = []
    for r in records:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r["lon"], r["lat"]]
            },
            "properties": {
                "cell_id":          r["cell_id"],
                "cell_area_ha":     CELL_AREA_HA,
                "grid_resolution_m": GRID_RESOLUTION_M,

                "static_terrain":   r["terrain"],

                "biological_fuel":  r["fuel"],

                "historical_fire":  r["historical"],

                "weather_sequence": {
                    "window_days":     WINDOW_DAYS,
                    "steps_per_day":   STEPS_PER_DAY,
                    "total_timesteps": TOTAL_TIMESTEPS,
                    "timesteps":       r["weather_seq"]
                },

                "target_labels": r["labels"]
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "name": "FireFusion_Training_Data",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}
        },
        "features": features
    }

def to_inference_json(records):
    cells = []
    for r in records:
        static_order = ["elevation_m", "slope_deg", "aspect_deg", "dist_to_water_m",
                        "veg_type_encoded", "ndvi_at_ignition", "ndwi_at_ignition", "nbr_at_ignition"]

        temporal_order = ["max_temp_c", "wind_speed_kmh", "wind_dir_deg", "rel_humidity_pct",
                          "precipitation_mm", "evapotranspiration", "soil_moisture",
                          "soil_temp_c", "days_since_rain", "years_since_last_fire"]

        static_vals = [
            r["terrain"]["elevation_m"],
            r["terrain"]["slope_deg"],
            r["terrain"]["aspect_deg"],
            r["terrain"]["dist_to_water_m"],
            r["fuel"]["veg_type_encoded"],
            r["fuel"]["ndvi_at_ignition"],
            r["fuel"]["ndwi_at_ignition"],
            r["fuel"]["nbr_at_ignition"],
        ]

        timesteps = []
        for step in r["weather_seq"]:
            timesteps.append({
                "day":    step["day"],
                "hour":   step["hour"],
                "values": [step[k] for k in temporal_order]
            })

        cells.append({
            "cell_id": r["cell_id"],
            "static_features": {
                "feature_order": static_order,
                "values": static_vals
            },
            "temporal_features": {
                "feature_order": temporal_order,
                "timesteps": timesteps
            }
        })

    return {
        "schema_version":   "2.0.0",
        "created_at":       datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "grid_resolution_m": GRID_RESOLUTION_M,
        "cell_area_ha":     CELL_AREA_HA,
        "forecast_horizon_h": 24,
        "tensor_shape": {
            "window_days":      WINDOW_DAYS,
            "steps_per_day":    STEPS_PER_DAY,
            "total_timesteps":  TOTAL_TIMESTEPS,
            "static_features":  8,
            "temporal_features": 10
        },
        "cells": cells
    }

# ── Stats summary ──────────────────────────────────────────────────────────────

def print_summary(records):
    labels    = [r["labels"] for r in records]
    severities= [l["severity_class"] for l in labels]
    areas     = [l["area_ha_burned"] for l in labels]
    ros       = [l["rate_of_spread_ha_per_day"] for l in labels]

    print("\n" + "="*55)
    print(f"SYNTHETIC DATASET SUMMARY  ({len(records)} records)")
    print("="*55)

    print("\nSeverity class distribution:")
    for s in range(1, 6):
        count = severities.count(s)
        bar = "█" * int(count / len(records) * 40)
        print(f"  Class {s}: {bar} {count:>4} ({count/len(records)*100:.1f}%)")

    print(f"\nArea burned (ha):")
    print(f"  Min:    {min(areas):>12.1f}")
    print(f"  Median: {sorted(areas)[len(areas)//2]:>12.1f}")
    print(f"  Max:    {max(areas):>12.1f}")

    print(f"\nRate of spread (ha/day):")
    print(f"  Min:    {min(ros):>12.1f}")
    print(f"  Median: {sorted(ros)[len(ros)//2]:>12.1f}")
    print(f"  Max:    {max(ros):>12.1f}")

    temps = [s["max_temp_c"] for r in records for s in r["weather_seq"] if s["day"] == 0 and s["hour"] == 18]
    winds = [s["wind_speed_kmh"] for r in records for s in r["weather_seq"] if s["day"] == 0 and s["hour"] == 18]
    print(f"\nIgnition-day peak conditions (day 0, 18:00):")
    print(f"  Avg temp:  {sum(temps)/len(temps):.1f} °C")
    print(f"  Avg wind:  {sum(winds)/len(winds):.1f} km/h")
    print("="*55)

# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FireFusion synthetic data generator")
    parser.add_argument("--n",    type=int, default=200, help="Number of records to generate (default: 200)")
    parser.add_argument("--seed", type=int, default=42,  help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--out",  type=str, default=".",  help="Output directory (default: current)")
    args = parser.parse_args()

    print(f"Generating {args.n} synthetic fire records (seed={args.seed})...")

    records = [generate_record(i, seed=args.seed) for i in range(args.n)]

    # Training GeoJSON
    training_data  = to_training_geojson(records)
    training_path  = f"{args.out}/firefusion_training.geojson"
    with open(training_path, "w") as f:
        json.dump(training_data, f, indent=2)
    print(f"Saved → {training_path}")

    # Inference JSON (first 5 records as sample)
    inference_data = to_inference_json(records[:5])
    inference_path = f"{args.out}/firefusion_inference_sample.json"
    with open(inference_path, "w") as f:
        json.dump(inference_data, f, indent=2)
    print(f"Saved → {inference_path}")

    print_summary(records)

if __name__ == "__main__":
    main()