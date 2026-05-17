"""
ERA5 Weather Integration Pipeline
FireFusion - Data Engineering Stream

Purpose:
- Prepare ERA5 weather data for integration into the weather_observation table.
- Match ERA5 records with Location Registry and Time Registry.
- Produce final schema-aligned output for Supabase integration.
"""

import pandas as pd
from scipy.spatial import cKDTree


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

ERA5_FILE = r"C:\Users\shubham sharma\Downloads\capstone\era5_victoria_jan2020_clean.csv"
LOCATION_REGISTRY_FILE = r"C:\Users\shubham sharma\Downloads\capstone\location_registry_rows.csv"
TIME_REGISTRY_FILE = r"C:\Users\shubham sharma\Downloads\capstone\time_registry_jan2020.csv"
OUTPUT_FILE = r"C:\Users\shubham sharma\Downloads\capstone\era5_weather_integrated.csv"


# ---------------------------------------------------------
# 2. Load datasets
# ---------------------------------------------------------

era5 = pd.read_csv(ERA5_FILE)
location_registry = pd.read_csv(LOCATION_REGISTRY_FILE)
time_registry = pd.read_csv(TIME_REGISTRY_FILE)


# ---------------------------------------------------------
# 3. Prepare ERA5 data
# ---------------------------------------------------------

era5 = era5.rename(columns={
    "lat": "original_latitude",
    "lon": "original_longitude",
    "temperature": "temperature_C"
})

era5_ready = era5[
    [
        "datetime",
        "original_latitude",
        "original_longitude",
        "temperature_C",
        "wind_speed"
    ]
].copy()

era5_ready["datetime"] = pd.to_datetime(era5_ready["datetime"])


# ---------------------------------------------------------
# 4. Filter records to Victoria bounds
# ---------------------------------------------------------

era5_ready = era5_ready[
    (era5_ready["original_latitude"] >= -39.2) &
    (era5_ready["original_latitude"] <= -34.0) &
    (era5_ready["original_longitude"] >= 140.96) &
    (era5_ready["original_longitude"] <= 150.0)
].copy()

print("Rows after Victoria filter:", era5_ready.shape)


# ---------------------------------------------------------
# 5. Match ERA5 coordinates to Location Registry
# ---------------------------------------------------------

registry_coords = location_registry[["grid_latitude", "grid_longitude"]].values
tree = cKDTree(registry_coords)

era5_coords = era5_ready[["original_latitude", "original_longitude"]].values
_, indices = tree.query(era5_coords)

era5_ready["location_id"] = location_registry.iloc[indices]["location_id"].values

print("Missing location_id:", era5_ready["location_id"].isnull().sum())


# ---------------------------------------------------------
# 6. Match ERA5 datetime to Time Registry
# ---------------------------------------------------------

time_registry["datetime_record"] = pd.to_datetime(time_registry["datetime_record"])

time_lookup = time_registry[["time_id", "datetime_record"]].copy()

era5_final = era5_ready.merge(
    time_lookup,
    left_on="datetime",
    right_on="datetime_record",
    how="left"
)

print("Missing time_id:", era5_final["time_id"].isnull().sum())


# ---------------------------------------------------------
# 7. Create final schema-aligned dataset
# ---------------------------------------------------------

era5_final = era5_final[
    [
        "location_id",
        "time_id",
        "original_latitude",
        "original_longitude",
        "temperature_C",
        "wind_speed"
    ]
]

era5_final.to_csv(OUTPUT_FILE, index=False)


# ---------------------------------------------------------
# 8. Final validation summary
# ---------------------------------------------------------

print("Final integrated ERA5 dataset saved.")
print("Output file:", OUTPUT_FILE)
print("Final shape:", era5_final.shape)
print("Missing values:")
print(era5_final.isnull().sum())
