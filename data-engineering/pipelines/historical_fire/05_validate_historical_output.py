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

print("\nCRS:")
print(gdf.crs)

print("\nRecord type counts:")
print(gdf["record_type"].value_counts(dropna=False))

print("\nGeometry types:")
print(gdf.geometry.geom_type.value_counts())

print("\nMissing geometries:")
print(gdf.geometry.isna().sum())

print("\nMissing values:")
print(gdf.isna().sum())

print("\nDuplicate full rows:")
print(gdf.drop(columns="geometry").duplicated().sum())

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

print("\nValidation completed successfully.")