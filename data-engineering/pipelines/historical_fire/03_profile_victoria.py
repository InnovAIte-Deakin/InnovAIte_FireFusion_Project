from pathlib import Path
import pandas as pd
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GDB_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Bushfire_Boundaries_Historical"
    / "Bushfire_Boundaries_Historical.gdb"
)

LAYER_NAME = "Bushfire_Boundaries_Historical"

print("=" * 60)
print("VICTORIAN HISTORICAL BUSHFIRE PROFILE")
print("=" * 60)

print("\nLoading dataset...")

df = gpd.read_file(
    GDB_PATH,
    layer=LAYER_NAME,
    ignore_geometry=True
)

# Filter Victoria
vic = df[df["state"] == "VIC (Victoria)"].copy()

print("\n1. VICTORIAN RECORDS")
print("-" * 60)
print("Total Victorian records:", len(vic))

print("\n2. FIRE TYPES")
print("-" * 60)
print(vic["fire_type"].value_counts(dropna=False))

# Select actual bushfires
vic_bushfires = vic[vic["fire_type"] == "Bushfire"].copy()

print("\n3. VICTORIAN BUSHFIRES")
print("-" * 60)
print("Total Victorian bushfires:", len(vic_bushfires))

# Convert ignition date
vic_bushfires["ignition_date"] = pd.to_datetime(
    vic_bushfires["ignition_date"],
    errors="coerce"
)

print("\n4. IGNITION DATE RANGE")
print("-" * 60)
print("Earliest:", vic_bushfires["ignition_date"].min())
print("Latest:", vic_bushfires["ignition_date"].max())

print("\n5. MISSING VALUES")
print("-" * 60)
print(vic_bushfires.isna().sum())

print("\n6. FIRE ID QUALITY")
print("-" * 60)
print("Missing IDs:", vic_bushfires["fire_id"].isna().sum())
print("Unique IDs:", vic_bushfires["fire_id"].nunique())
print(
    "Duplicate non-null IDs:",
    vic_bushfires["fire_id"].dropna().duplicated().sum()
)

print("\n7. AGENCIES")
print("-" * 60)
print(vic_bushfires["agency"].value_counts(dropna=False))

print("\n8. SAMPLE RECORDS")
print("-" * 60)

sample_columns = [
    "fire_id",
    "fire_name",
    "ignition_date",
    "fire_type",
    "ignition_cause",
    "area_ha",
    "perim_km",
    "agency"
]

print(vic_bushfires[sample_columns].head(10).to_string(index=False))

print("\nVictorian bushfire profiling completed successfully.")