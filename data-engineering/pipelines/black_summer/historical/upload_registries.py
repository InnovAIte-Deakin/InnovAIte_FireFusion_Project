import pandas as pd
import os
from dotenv import load_dotenv

from pipelines.common.db_connection import engine

load_dotenv()

DATA_ROOT = os.getenv("DATA_ROOT")

# =========================
# LOAD LOCATION REGISTRY
# =========================

location_file = os.path.join(
    DATA_ROOT,
    "processed",
    "location_registry.csv"
)

print("Loading location registry...")

location_df = pd.read_csv(location_file)

print(location_df.head())

# =========================
# LOAD TIME REGISTRY
# =========================

time_file = os.path.join(
    DATA_ROOT,
    "processed",
    "time_registry.csv"
)

print("\nLoading time registry...")

time_df = pd.read_csv(time_file)

print(time_df.head())

# =========================
# UPLOAD LOCATION REGISTRY
# =========================

print("\nUploading location registry...")

location_df.to_sql(
    "location_registry",
    engine,
    if_exists="append",
    index=False
)

print("Location registry uploaded")

# =========================
# UPLOAD TIME REGISTRY
# =========================

print("\nUploading time registry...")

time_df.to_sql(
    "time_registry",
    engine,
    if_exists="append",
    index=False
)

print("Time registry uploaded")

print("\nRegistry upload complete")