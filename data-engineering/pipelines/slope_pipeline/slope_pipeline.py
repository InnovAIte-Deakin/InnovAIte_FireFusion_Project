#!/usr/bin/env python
# coding: utf-8

# In[1]:


import srtm
import pandas as pd
import numpy as np
import os
from IPython.display import FileLink

# =========================
# 1: Generating grid
# =========================
def generate_grid(lat_min, lat_max, lon_min, lon_max, step):
    lats = np.arange(lat_min, lat_max, step)
    lons = np.arange(lon_min, lon_max, step)
    return lats, lons

# =========================
# 2: Getting elevation
# =========================
def get_elevation_data(lats, lons):
    elevation_data = srtm.get_data()
    data = []

    for lat in lats:
        for lon in lons:
            elevation = elevation_data.get_elevation(lat, lon)
            data.append([lat, lon, elevation])

    df = pd.DataFrame(data, columns=["lat", "lon", "elevation"])
    return df

# =========================
# 3: Cleaning data 
# =========================
def clean_data(df):
    df = df.dropna()
    df = df[df["elevation"] > 0]  # remove ocean/invalid values
    df = df.reset_index(drop=True)
    return df

# =========================
# 4: Computing the slope
# =========================
def compute_slope(df):
    df["slope"] = np.abs(np.gradient(df["elevation"]))
    return df

# =========================
# 5: Saveing dataset
# =========================
def save_data(df, file_name):
    df.to_csv(file_name, index=False)
    print(f"Dataset saved as {file_name}")

# =========================
# MAIN PIPELINE
# =========================
def run_pipeline():
    # Victoria bounds
    lat_min, lat_max = -39, -34
    lon_min, lon_max = 140, 150
    step = 0.5

    print("Generating grid...")
    lats, lons = generate_grid(lat_min, lat_max, lon_min, lon_max, step)

    print("Fetching elevation...")
    df = get_elevation_data(lats, lons)

    print("Cleaning data...")
    df = clean_data(df)

    print("Computing slope...")
    df = compute_slope(df)

    print("Saving dataset...")
    file_name = "victoria_slope_pipeline.csv"
    save_data(df, file_name)

    print("\nPipeline completed!")
    print(df.head())
    print("\nTotal rows:", len(df))

# Running pipeline
run_pipeline()

