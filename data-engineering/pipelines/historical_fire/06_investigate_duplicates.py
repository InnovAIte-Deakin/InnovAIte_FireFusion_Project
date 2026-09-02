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
print("INVESTIGATING POSSIBLE DUPLICATE FIRE RECORDS")
print("=" * 60)

gdf = gpd.read_file(FILE)

non_geometry_columns = [
    column
    for column in gdf.columns
    if column != "geometry"
]

duplicate_mask = gdf.duplicated(
    subset=non_geometry_columns,
    keep=False
)

duplicates = gdf[duplicate_mask].copy()

print("\nRecords involved in duplicate groups:")
print(len(duplicates))

print("\nNumber of duplicate groups:")
print(
    duplicates.groupby(non_geometry_columns, dropna=False)
    .ngroups
)

# Check whether entire geometry is also duplicated
exact_duplicates = gdf.duplicated(
    subset=non_geometry_columns + ["geometry"],
    keep=False
)

print("\nRecords with identical attributes AND geometry:")
print(exact_duplicates.sum())

print("\nSample possible duplicates:")
print(
    duplicates[
        [
            "fire_id",
            "fire_name",
            "ignition_date",
            "area_ha",
            "perim_km",
            "state",
            "agency",
        ]
    ]
    .head(20)
    .to_string(index=False)
)

print("\nDuplicate investigation completed.")