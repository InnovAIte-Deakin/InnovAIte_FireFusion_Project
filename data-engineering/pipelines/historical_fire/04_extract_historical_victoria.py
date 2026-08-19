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
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "victoria_historical_bushfires.geojson"

LAYER_NAME = "Bushfire_Boundaries_Historical"

print("=" * 60)
print("EXTRACTING VICTORIAN HISTORICAL BUSHFIRES")
print("=" * 60)

print("\nLoading Victorian bushfire records...")

# Read only the records we actually need
gdf = gpd.read_file(
    GDB_PATH,
    layer=LAYER_NAME,
    where=(
        "state = 'VIC (Victoria)' "
        "AND fire_type = 'Bushfire'"
    )
)

print("Records extracted:", len(gdf))

# Keep fields required by the project
columns = [
    "fire_id",
    "fire_name",
    "ignition_date",
    "capture_date",
    "extinguish_date",
    "fire_type",
    "ignition_cause",
    "area_ha",
    "perim_km",
    "state",
    "agency",
    "geometry",
]

gdf = gdf[columns].copy()

# Mark these as historical records
gdf["record_type"] = "HISTORICAL"

print("\nOriginal CRS:", gdf.crs)

# Validate the expected source CRS before reprojection
assert gdf.crs is not None, "Source CRS is missing."

assert gdf.crs.to_epsg() == 4283, (
    f"Unexpected source CRS: {gdf.crs}. Expected EPSG:4283."
)

# Convert to the CRS commonly used by PostGIS/web mapping
gdf = gdf.to_crs(epsg=4326)

print("Output CRS:", gdf.crs)

# Check geometry
print("\nGeometry types:")
print(gdf.geometry.geom_type.value_counts())

print("\nMissing geometries:")
print(gdf.geometry.isna().sum())

print("\nRecord type:")
print(gdf["record_type"].value_counts())

# Remove only records that are exact duplicates
records_before = len(gdf)

gdf = gdf.drop_duplicates(
    subset=[
        "fire_id",
        "fire_name",
        "ignition_date",
        "capture_date",
        "extinguish_date",
        "fire_type",
        "ignition_cause",
        "area_ha",
        "perim_km",
        "state",
        "agency",
        "record_type",
        "geometry",
    ]
).copy()

duplicates_removed = records_before - len(gdf)

print("\nDuplicate handling:")
print("Exact duplicate records removed:", duplicates_removed)
print("Final records:", len(gdf))

# Save processed data
print("\nSaving historical bushfire dataset...")

gdf.to_file(
    OUTPUT_FILE,
    driver="GeoJSON"
)

print("\nOutput saved to:")
print(OUTPUT_FILE)

print("\nHistorical fire extraction completed successfully.")