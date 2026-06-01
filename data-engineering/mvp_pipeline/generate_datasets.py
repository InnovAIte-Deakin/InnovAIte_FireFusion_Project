"""
FireFusion Realistic Dataset Generator

Generates synthetic Black Summer 2019-2020 data for Victoria.
Used for testing MVP pipeline before loading real data sources.

Outputs:
  - fire_sample.csv: Fire incidents with confidence scores
  - weather_sample.csv: Temperature, wind, humidity
  - vegetation_sample.csv: Dryness index, soil moisture
  - topography_sample.csv: Elevation, slope (static)
  - infrastructure_sample.csv: Facilities, risk category (static)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

os.makedirs("input", exist_ok=True)

VIC_LOCATIONS = [
    (-37.8147, 145.0892, "Melbourne"),
    (-38.1500, 144.3600, "Geelong"),
    (-36.7500, 144.2800, "Bendigo"),
    (-37.5600, 143.8500, "Ballarat"),
    (-36.0700, 146.9100, "Wodonga"),
    (-38.3300, 141.6100, "Warrnambool"),
    (-37.8300, 147.9900, "Bairnsdale"),
    (-36.3600, 145.4000, "Shepparton"),
    (-37.1200, 143.1200, "Ararat"),
    (-36.9900, 141.8800, "Hamilton"),
    (-37.6200, 143.5500, "Bacchus Marsh"),
    (-38.2200, 142.2200, "Colac"),
    (-37.2200, 144.6600, "Castlemaine"),
    (-36.5500, 145.8800, "Wangaratta"),
    (-37.1200, 146.5800, "Bairnsdale"),
]

START = datetime(2019, 6, 1)
END = datetime(2020, 3, 31)
DATES = pd.date_range(START, END, freq="D")

print("=" * 70)
print("FireFusion Dataset Generator")
print("=" * 70)

# FIRE INCIDENT RECORD
print("\nGenerating fire_incident_record...")
records = []
incident_id = 1

for date in DATES:
    month = date.month
    fire_prob = 0.85 if month in [12, 1, 2] else 0.5 if month in [11, 3] else 0.1
    
    for lat, lon, region in VIC_LOCATIONS:
        if np.random.random() < fire_prob:
            records.append({
                'incident_id': incident_id,
                'original_latitude': round(lat + np.random.uniform(-0.05, 0.05), 4),
                'original_longitude': round(lon + np.random.uniform(-0.05, 0.05), 4),
                'confidence_score': np.random.choice([60, 70, 80, 85, 90, 95, 100]),
                'source_system': 'Black_Summer_Historical',
                'datetime_record': date.strftime('%Y-%m-%dT%H:%M:%S'),
            })
            incident_id += 1

df_fire = pd.DataFrame(records)
df_fire.to_csv("input/fire_sample.csv", index=False)
print("  {} fire records".format(len(df_fire)))

# WEATHER OBSERVATION
print("Generating weather_observation...")
records = []
weather_id = 1

for date in DATES:
    month = date.month
    base_temp = 10 if month in [6, 7, 8] else 28 if month in [12, 1, 2] else 18
    
    for lat, lon, region in VIC_LOCATIONS:
        for hour_offset in [0, 8, 16]:
            temp = round(base_temp + np.random.uniform(-5, 5), 1)
            wind = round(np.random.uniform(5, 40), 1)
            humidity = round(np.random.uniform(20, 90), 1)
            
            records.append({
                'weather_id': weather_id,
                'original_latitude': round(lat + np.random.uniform(-0.02, 0.02), 4),
                'original_longitude': round(lon + np.random.uniform(-0.02, 0.02), 4),
                'temperature_c': temp,
                'wind_speed_kmh': wind,
                'relative_humidity': humidity,
                'source_system': 'Open-Meteo',
                'datetime_record': (date + timedelta(hours=hour_offset)).strftime('%Y-%m-%dT%H:%M:%S'),
            })
            weather_id += 1

df_weather = pd.DataFrame(records)
df_weather.to_csv("input/weather_sample.csv", index=False)
print("  {} weather records".format(len(df_weather)))

# VEGETATION CONDITION
print("Generating vegetation_condition...")
records = []
veg_id = 1
VEG_CLASSES = ["dense", "moderate", "sparse", "bare"]

for date in DATES[::3]:
    month = date.month
    base_dry = 0.85 if month in [12, 1, 2] else 0.55 if month in [11, 3] else 0.35
    
    for lat, lon, region in VIC_LOCATIONS:
        dryness = round(min(1.0, max(0.0, base_dry + np.random.uniform(-0.1, 0.1))), 3)
        moisture = round(min(1.0, max(0.0, 1.0 - dryness + np.random.uniform(-0.05, 0.05))), 3)
        
        records.append({
            'veg_condition_id': veg_id,
            'original_latitude': round(lat + np.random.uniform(-0.03, 0.03), 4),
            'original_longitude': round(lon + np.random.uniform(-0.03, 0.03), 4),
            'dryness_index': dryness,
            'soil_moisture': moisture,
            'vegetation_class': np.random.choice(VEG_CLASSES),
            'source_system': 'SMAP_NASA',
            'datetime_record': date.strftime('%Y-%m-%dT%H:%M:%S'),
        })
        veg_id += 1

df_veg = pd.DataFrame(records)
df_veg.to_csv("input/vegetation_sample.csv", index=False)
print("  {} vegetation records".format(len(df_veg)))

# TOPOGRAPHY PROFILE (Static)
print("Generating topography_profile...")
records = []

REGION_ELEVATIONS = {
    "Melbourne": (50, 200), "Geelong": (20, 150), "Bendigo": (200, 350),
    "Ballarat": (400, 550), "Wodonga": (150, 300), "Warrnambool": (10, 100),
    "Bairnsdale": (20, 150), "Shepparton": (80, 160), "Ararat": (300, 450),
    "Hamilton": (200, 350), "Bacchus Marsh": (100, 300), "Colac": (80, 200),
    "Castlemaine": (300, 450), "Wangaratta": (150, 300), "Bairnsdale": (50, 200),
}

for i, (lat, lon, region) in enumerate(VIC_LOCATIONS, 1):
    elev_min, elev_max = REGION_ELEVATIONS.get(region, (50, 400))
    records.append({
        'topo_id': i,
        'original_latitude': lat,
        'original_longitude': lon,
        'elevation_m': round(np.random.uniform(elev_min, elev_max), 1),
        'slope_angle': round(np.random.uniform(0, 35), 1),
    })

df_topo = pd.DataFrame(records)
df_topo.to_csv("input/topography_sample.csv", index=False)
print("  {} topography records".format(len(df_topo)))

# INFRASTRUCTURE ASSET (Static)
print("Generating infrastructure_asset...")
records = []

FACILITIES = [
    ("Hospital", "CAT 4"), ("Emergency Dept", "CAT 4"),
    ("Primary School", "CAT 4"), ("High School", "CAT 4"),
    ("Fire Station", "CAT 3"), ("Police Station", "CAT 3"),
    ("Power Substation", "CAT 2"), ("Water Treatment", "CAT 2"),
    ("Community Centre", "CAT 1"), ("Library", "CAT 0"),
]

asset_id = 1
for lat, lon, region in VIC_LOCATIONS:
    facility_indices = np.random.choice(len(FACILITIES), 4, replace=False)
    for idx in facility_indices:
        fac_name, risk_cat = FACILITIES[idx]
        records.append({
            'asset_id': asset_id,
            'original_latitude': round(lat + np.random.uniform(-0.05, 0.05), 4),
            'original_longitude': round(lon + np.random.uniform(-0.05, 0.05), 4),
            'facility_name': "{} {}".format(region, fac_name),
            'risk_category': risk_cat,
        })
        asset_id += 1

df_infra = pd.DataFrame(records)
df_infra.to_csv("input/infrastructure_sample.csv", index=False)
print("  {} infrastructure records".format(len(df_infra)))

print("\n" + "=" * 70)
print("Dataset generation complete")
print("=" * 70)