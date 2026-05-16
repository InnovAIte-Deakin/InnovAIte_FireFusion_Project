# =========================================================
# ERA5 Data Processing for FireFusion
# InnovAIte - Data Engineering Stream
# Contributor: Shubham Sharma
# =========================================================

"""
Objective:
Preprocess ERA5 weather data for Victoria during the Black Summer bushfires.

Variables used:
- 2m temperature
- 10m u-component of wind
- 10m v-component of wind
- Total precipitation

Output:
A cleaned CSV dataset saved in the processed data folder.
"""

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =========================================================
# 1. Load ERA5 Raw Data
# =========================================================

accumulated_path = r"C:\Users\shubham sharma\Downloads\capstone\data\raw\data_stream-oper_stepType-accum.nc"
instant_path = r"C:\Users\shubham sharma\Downloads\capstone\data\raw\data_stream-oper_stepType-instant.nc"

ds1 = xr.open_dataset(accumulated_path)
ds2 = xr.open_dataset(instant_path)


# =========================================================
# 2. Merge Datasets
# =========================================================

combined = xr.merge([ds1, ds2])


# =========================================================
# 3. Convert to Tabular Format
# =========================================================

df = combined.to_dataframe().reset_index()


# =========================================================
# 4. Clean and Rename Columns
# =========================================================

df = df.drop(columns=["number", "expver"], errors="ignore")

df = df.rename(columns={
    "valid_time": "datetime",
    "latitude": "lat",
    "longitude": "lon",
    "tp": "precipitation",
    "u10": "wind_u",
    "v10": "wind_v",
    "t2m": "temperature"
})


# =========================================================
# 5. Unit Conversion
# =========================================================

df["temperature"] = df["temperature"] - 273.15
df["precipitation"] = df["precipitation"] * 1000


# =========================================================
# 6. Feature Engineering
# =========================================================

df["wind_speed"] = np.sqrt(df["wind_u"] ** 2 + df["wind_v"] ** 2)
df["datetime"] = pd.to_datetime(df["datetime"])


# =========================================================
# 7. Save Processed Dataset
# =========================================================

output_path = r"C:\Users\shubham sharma\Downloads\capstone\data\processed\era5_victoria_jan2020_clean.csv"

df.to_csv(output_path, index=False)


# =========================================================
# 8. Validation Checks
# =========================================================

print("Processed dataset saved successfully.")
print("Dataset shape:", df.shape)
print("\nFirst five rows:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())

print("\nSummary statistics:")
print(df.describe())


# =========================================================
# 9. Basic EDA Plots
# =========================================================

df["temperature"].hist(bins=50)
plt.title("Temperature Distribution (°C)")
plt.xlabel("Temperature (°C)")
plt.ylabel("Frequency")
plt.show()

df["wind_speed"].hist(bins=50)
plt.title("Wind Speed Distribution")
plt.xlabel("Wind Speed")
plt.ylabel("Frequency")
plt.show()

daily = df.groupby("datetime")["temperature"].mean()
daily.plot(figsize=(10, 4), title="Temperature Over Time")
plt.xlabel("Datetime")
plt.ylabel("Average Temperature (°C)")
plt.show()