from pathlib import Path
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "victoria_historical_bushfires.geojson"
)

print("=" * 60)
print("VALIDATING HISTORICAL FIRE OUTPUT")
print("=" * 60)

gdf = gpd.read_file(FILE)

print("\nRows:", len(gdf))
print("Columns:", len(gdf.columns))

# Validate dataset is not empty
assert len(gdf) > 0, "Validation failed: output dataset is empty."

print("\nCRS:")
print(gdf.crs)

# Validate output CRS
assert gdf.crs is not None, "Validation failed: output CRS is missing."
assert gdf.crs.to_epsg() == 4326, (
    f"Validation failed: expected EPSG:4326, found {gdf.crs}."
)

print("\nRecord type counts:")
print(gdf["record_type"].value_counts(dropna=False))

# Validate record type
assert (gdf["record_type"] == "HISTORICAL").all(), (
    "Validation failed: non-HISTORICAL records found."
)

print("\nGeometry types:")
print(gdf.geometry.geom_type.value_counts())

# Validate geometry type
assert gdf.geometry.geom_type.eq("MultiPolygon").all(), (
    "Validation failed: geometry types other than MultiPolygon found."
)

print("\nMissing geometries:")
missing_geometries = gdf.geometry.isna().sum()
print(missing_geometries)

# Validate that all records contain geometry
assert missing_geometries == 0, (
    f"Validation failed: {missing_geometries} missing geometries found."
)

print("\nMissing values:")
print(gdf.isna().sum())

print("\nDuplicate full rows:")
duplicate_rows = gdf.duplicated().sum()
print(duplicate_rows)

# Exact duplicates should already have been removed during extraction
assert duplicate_rows == 0, (
    f"Validation failed: {duplicate_rows} exact duplicate rows found."
)

print("\nSample records:")
print(
    gdf[
        [
            "fire_id",
            "fire_name",
            "ignition_date",
            "fire_type",
            "area_ha",
            "state",
            "agency",
            "record_type",
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\nAll validation checks passed successfully.")