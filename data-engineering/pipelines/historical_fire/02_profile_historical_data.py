from pathlib import Path
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
print("HISTORICAL BUSHFIRE DATA PROFILE")
print("=" * 60)

print("\nLoading dataset metadata...")

# Geometry is not required for profiling, so don't load it.
gdf = gpd.read_file(
    GDB_PATH,
    layer=LAYER_NAME,
    ignore_geometry=True
)

print("\n1. DATASET SIZE")
print("-" * 60)
print("Rows:", len(gdf))
print("Columns:", len(gdf.columns))

print("\n2. RECORDS BY STATE")
print("-" * 60)
print(gdf["state"].value_counts(dropna=False))

print("\n3. FIRE TYPES")
print("-" * 60)
print(gdf["fire_type"].value_counts(dropna=False))

print("\n4. DATE RANGE")
print("-" * 60)

ignition_dates = gpd.pd.to_datetime(
    gdf["ignition_date"],
    errors="coerce"
)

print("Earliest ignition date:", ignition_dates.min())
print("Latest ignition date:", ignition_dates.max())

print("\n5. MISSING VALUES")
print("-" * 60)
print(gdf.isna().sum())

print("\n6. FIRE ID CHECK")
print("-" * 60)
print("Unique fire IDs:", gdf["fire_id"].nunique())
print("Missing fire IDs:", gdf["fire_id"].isna().sum())
print(
    "Duplicate non-null fire IDs:",
    gdf["fire_id"].dropna().duplicated().sum()
)

print("\nProfiling completed successfully.")